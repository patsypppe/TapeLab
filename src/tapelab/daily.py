"""Brings everything up to date for a watchlist in one go: python -m tapelab.daily AAPL MSFT NVDA.

Per ticker it refreshes prices, checks for a new 10-K, makes the day's decision (scoring a new filing
once) and saves the 10-day forecast. Each step is isolated, so one failure never stops the others,
and every step ignores work that is already done, so running it twice is harmless.
"""
import argparse
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import httpx
import psycopg

from .agents.gemini import GeminiLLM
from .agents.llm import LLM, RuleBasedLLM
from .db import connect
from .decide import make_decision
from .edgar import list_filings, sec_client
from .filings import load_filing
from .predict import make_forecast
from .prices import PriceRow, fetch_prices, latest_price_date, save_prices

log = logging.getLogger("tapelab.daily")

MARKET_TZ = ZoneInfo("America/New_York")
DATA_READY = time(16, 30)  # a day's price bar is final shortly after the 4pm close
STALE_AFTER_DAYS = 4  # a weekend plus a holiday is fine; more than this means the data has stopped arriving
FIRST_LOAD_DAYS = 400  # how far back to go for a ticker with no prices yet
REFRESH_DAYS = 7  # re-fetch this much already-stored history, to pick up price adjustments

PriceFetcher = Callable[[str, date, date], list[PriceRow]]  # ticker, start, end (exclusive)
FilingLoader = Callable[[psycopg.Connection, str], tuple[str, str]]  # returns (status, detail)


@dataclass(frozen=True)
class StepResult:
    ticker: str
    step: str  # prices, filing, decision or forecast
    status: str  # done, unchanged, skipped, warning or failed
    detail: str


def last_complete_day(now: datetime) -> date:
    """The latest day whose price bar is final: today after 4:30pm New York time, otherwise yesterday."""
    local = now.astimezone(MARKET_TZ)
    return local.date() if local.time() >= DATA_READY else local.date() - timedelta(days=1)


def _attempt(conn: psycopg.Connection, ticker: str, step: str, work: Callable[[], tuple[str, str]]) -> StepResult:
    """Run one step; any error becomes a 'failed' result instead of stopping the job."""
    try:
        status, detail = work()
    except Exception as error:
        conn.rollback()  # a failed SQL statement leaves the connection unusable until rolled back
        log.exception("%s %s failed", ticker, step)
        return StepResult(ticker, step, "failed", f"{type(error).__name__}: {error}")
    log.info("%s %s %s: %s", ticker, step, status, detail)
    return StepResult(ticker, step, status, detail)


def run_daily(conn: psycopg.Connection, tickers: list[str], fetch: PriceFetcher, load_new_filing: FilingLoader,
              get_llm: Callable[[], LLM], now: datetime) -> list[StepResult]:
    """Run every step for every ticker and report what happened. Never raises for a step's failure."""
    end_day = last_complete_day(now)
    results: list[StepResult] = []
    for ticker in (t.upper() for t in tickers):

        def refresh_prices(ticker: str = ticker) -> tuple[str, str]:
            latest = latest_price_date(conn, ticker)
            start = latest - timedelta(days=REFRESH_DAYS) if latest else end_day - timedelta(days=FIRST_LOAD_DAYS)
            rows = [r for r in fetch(ticker, start, end_day + timedelta(days=1)) if r.date <= end_day]
            save_prices(conn, rows)
            new_days = sum(1 for r in rows if latest is None or r.date > latest)
            if new_days == 0:
                return "unchanged", f"no new days (latest {latest})"
            return "done", f"{new_days} new day(s), latest {max(r.date for r in rows)}"

        results.append(_attempt(conn, ticker, "prices", refresh_prices))
        results.append(_attempt(conn, ticker, "filing", lambda ticker=ticker: load_new_filing(conn, ticker)))

        day = latest_price_date(conn, ticker)
        if day is None:
            for step in ("decision", "forecast"):
                results.append(StepResult(ticker, step, "skipped", "no prices for this ticker"))
            continue
        if (end_day - day).days > STALE_AFTER_DAYS:
            detail = f"latest price is {day}, {(end_day - day).days} days before {end_day}; the data may have stopped updating"
            log.warning("%s %s", ticker, detail)
            results.append(StepResult(ticker, "prices", "warning", detail))

        def decide_today(ticker: str = ticker, day: date = day) -> tuple[str, str]:
            saved = make_decision(conn, get_llm(), ticker, day)
            stance = "LONG" if saved.position >= 1 else "FLAT"
            return ("done", f"{stance} for {day}") if saved.created else ("unchanged", f"{stance} for {day}, already decided")

        def forecast_today(ticker: str = ticker, day: date = day) -> tuple[str, str]:
            saved = make_forecast(conn, ticker, day)
            last = saved.points[-1]
            text = f"10-day range from the {day} close: {last['low']:.2f} to {last['high']:.2f} by {last['date']}"
            return ("done", text) if saved.created else ("unchanged", text + ", already made")

        results.append(_attempt(conn, ticker, "decision", decide_today))
        results.append(_attempt(conn, ticker, "forecast", forecast_today))
    return results


def format_summary(results: list[StepResult]) -> str:
    """A short report: each ticker's steps, then a count of how it went."""
    lines: list[str] = []
    for ticker in dict.fromkeys(r.ticker for r in results):
        lines.append(ticker)
        lines += [f"  {r.step:<9}{r.status:<10}{r.detail}" for r in results if r.ticker == ticker]
    counts = {s: sum(r.status == s for r in results) for s in ("done", "unchanged", "skipped", "warning", "failed")}
    lines.append("\n" + ", ".join(f"{n} {s}" for s, n in counts.items() if n))
    return "\n".join(lines)


def exit_code(results: list[StepResult]) -> int:
    """1 if any step failed, so a scheduler or log watcher can notice; warnings and skips are not failures."""
    return 1 if any(r.status == "failed" for r in results) else 0


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Refresh prices, filings, decisions and forecasts for a watchlist")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--llm", choices=["gemini", "rule"], default="gemini")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    sec: list[httpx.Client] = []  # created on first use, so a missing SEC_USER_AGENT only fails the filing step

    def load_new_filing(conn: psycopg.Connection, ticker: str) -> tuple[str, str]:
        if not sec:
            sec.append(sec_client())
        refs = list_filings(sec[0], ticker, "10-K", 1)
        if not refs:
            return "unchanged", "no 10-K found"
        chunks = load_filing(conn, sec[0], refs[0])
        if chunks is None:
            return "unchanged", f"10-K filed {refs[0].filed_at} already saved"
        return "done", f"new 10-K filed {refs[0].filed_at}: {len(chunks)} chunks"

    with httpx.Client(timeout=30) as yahoo, connect() as conn:
        results = run_daily(conn, args.tickers, lambda t, s, e: fetch_prices(t, s, e, yahoo), load_new_filing,
                            GeminiLLM if args.llm == "gemini" else RuleBasedLLM, datetime.now().astimezone())
    for client in sec:
        client.close()
    print(format_summary(results))
    sys.exit(exit_code(results))


if __name__ == "__main__":
    main()
