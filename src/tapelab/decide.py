"""Makes and saves one decision per ticker per day: python -m tapelab.decide AAPL."""
import argparse
from dataclasses import dataclass
from datetime import date

import psycopg
from psycopg.types.json import Jsonb

from .agents.fundamentals import latest_filing_before, score_filing
from .agents.gemini import GeminiLLM
from .agents.llm import LLM, RuleBasedLLM
from .agents.technical import technical_signal
from .agents.trader import decide
from .agents.types import Signal
from .db import connect
from .prices import closes_through, has_price_on, latest_price_date

HISTORY = 60  # closing prices handed to the technical analyst
FAST, SLOW = 10, 30  # moving-average windows, in trading days


@dataclass(frozen=True)
class SavedDecision:
    ticker: str
    decided_for: date
    position: float
    signals: tuple[Signal, ...]
    filing_id: int | None
    created: bool  # False when this ticker and day had already been decided


def _stored(conn: psycopg.Connection, ticker: str, day: date) -> SavedDecision:
    position, reasons, filing_id = conn.execute(
        "SELECT position, reasons, filing_id FROM decisions WHERE ticker = %s AND decided_for = %s",
        (ticker, day),
    ).fetchone()
    signals = tuple(Signal(r["analyst"], r["score"], r["rationale"]) for r in reasons)
    return SavedDecision(ticker, day, float(position), signals, filing_id, created=False)


def make_decision(conn: psycopg.Connection, llm: LLM, ticker: str, as_of: date) -> SavedDecision:
    """Decide for the close of as_of using only data available then, and save it once."""
    ticker = ticker.upper()
    if not has_price_on(conn, ticker, as_of):
        raise ValueError(f"No {ticker} price on {as_of}; it was not a trading day or is not loaded")
    signals = [technical_signal(closes_through(conn, ticker, as_of, HISTORY), FAST, SLOW)]
    filing = latest_filing_before(conn, ticker, as_of)
    filing_id = filing[0] if filing else None
    if filing_id is not None:
        signals.append(score_filing(conn, llm, filing_id))
    decision = decide(signals)
    reasons = [{"analyst": s.analyst, "score": s.score, "rationale": s.rationale} for s in signals]
    config = {"model": getattr(llm, "model", None) or type(llm).__name__,
              "technical": {"fast": FAST, "slow": SLOW}, "weights": "equal"}
    row = conn.execute(
        "INSERT INTO decisions (ticker, decided_for, position, reasons, config, filing_id) "
        "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (ticker, decided_for) DO NOTHING RETURNING id",
        (ticker, as_of, decision.position, Jsonb(reasons), Jsonb(config), filing_id),
    ).fetchone()
    conn.commit()
    if row is None:
        return _stored(conn, ticker, as_of)  # a day cannot be redone: show what was saved
    return SavedDecision(ticker, as_of, decision.position, tuple(signals), filing_id, created=True)


def main() -> None:
    """Command-line entry point; prints one decision per ticker."""
    parser = argparse.ArgumentParser(description="Make and save today's decision for each ticker")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--as-of", type=date.fromisoformat,
                        help="decide for the close of this day (default: the latest day with a price)")
    parser.add_argument("--llm", choices=["gemini", "rule"], default="gemini")
    args = parser.parse_args()
    llm = GeminiLLM() if args.llm == "gemini" else RuleBasedLLM()
    with connect() as conn:
        for ticker in args.tickers:
            day = args.as_of or latest_price_date(conn, ticker)
            if day is None:
                print(f"{ticker.upper()}: no prices loaded (run python -m tapelab.prices first)")
                continue
            result = make_decision(conn, llm, ticker, day)
            stance = "LONG" if result.position >= 1 else "FLAT"
            note = "saved" if result.created else "already decided, showing the saved decision"
            print(f"{result.ticker} for the close of {result.decided_for}: {stance} ({note})")
            for s in result.signals:
                print(f"  {s.analyst:<13}{s.score:+.2f}  {s.rationale}")


if __name__ == "__main__":
    main()
