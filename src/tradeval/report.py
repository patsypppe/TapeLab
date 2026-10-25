"""Prints how each trend rule did against buy-and-hold: python -m tradeval.report AAPL MSFT NVDA."""
import argparse
from datetime import date

import psycopg

from tapelab.db import connect

from .compare import MIN_DAYS_SCORED, Result, run_comparison
from .rules import TrendRule

DEFAULT_WINDOWS = ["5/20", "10/30", "20/50", "50/200"]


def load_history(conn: psycopg.Connection, ticker: str) -> tuple[list[date], list[float]]:
    """Every stored day for a ticker, oldest first, as dates and closing prices."""
    rows = conn.execute("SELECT date, close FROM prices WHERE ticker = %s ORDER BY date", (ticker.upper(),)).fetchall()
    return [r[0] for r in rows], [float(r[1]) for r in rows]


def parse_windows(texts: list[str]) -> list[TrendRule]:
    """Turn ['10/30', '50/200'] into rules, rejecting windows where fast is not shorter than slow."""
    rules = []
    for text in texts:
        fast, slow = (int(part) for part in text.split("/"))
        if not 0 < fast < slow:
            raise ValueError(f"Window {text!r}: the fast window must be shorter than the slow one")
        rules.append(TrendRule(fast, slow))
    return rules


def format_table(results: list[Result]) -> str:
    """One row per rule: return, risk numbers, how often it traded and how often it held the stock."""
    lines = [f"{'rule':<14}{'return':>9}{'sharpe':>8}{'sortino':>9}{'max drop':>10}{'trades':>8}{'invested':>10}"]
    for r in results:
        lines.append(f"{r.name:<14}{r.total_return:>+9.1%}{r.sharpe:>8.2f}{r.sortino:>9.2f}"
                     f"{-r.max_drawdown:>10.1%}{r.trades:>8}{r.invested:>10.0%}")
    return "\n".join(lines)


def build_report(conn: psycopg.Connection, tickers: list[str], rules: list[TrendRule], cost_bps: float) -> str:
    """The full text report for all tickers, ending with a reminder of how many variants were tried."""
    start = max(rule.slow for rule in rules)
    blocks = []
    tested = 0  # tickers that actually had enough prices to run
    for ticker in tickers:
        dates, closes = load_history(conn, ticker)
        if not closes:
            blocks.append(f"{ticker.upper()}: no prices loaded (run python -m tapelab.prices first)")
        elif len(closes) - 1 - start < MIN_DAYS_SCORED:
            blocks.append(f"{ticker.upper()}: only {len(closes)} days of prices, need at least "
                          f"{start + MIN_DAYS_SCORED + 1}")
        else:
            scored = len(closes) - 1 - start
            header = (f"{ticker.upper()}: {dates[0]} to {dates[-1]}, {len(closes)} days; "
                      f"scored over the last {scored} days (from {dates[start]})")
            blocks.append(header + "\n" + format_table(run_comparison(closes, rules, cost_bps)))
            tested += 1
    runs = len(rules) * tested
    blocks.append(f"Costs: {cost_bps:g} basis points on each position change. Variants tried: {len(rules)} rules "
                  f"on {tested} ticker{'s' if tested != 1 else ''} = {runs} runs, plus buy and hold.\n"
                  "With this many variants the best-looking row is partly luck, and a few stocks over one "
                  "period say little about the future. Do not pick a winner from this table alone.")
    return "\n\n".join(blocks)


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Compare trend rules with buy-and-hold on stored prices")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--windows", nargs="+", default=DEFAULT_WINDOWS, help="fast/slow pairs, e.g. 10/30")
    parser.add_argument("--cost-bps", type=float, default=5.0)
    args = parser.parse_args()
    with connect() as conn:
        print(build_report(conn, args.tickers, parse_windows(args.windows), args.cost_bps))


if __name__ == "__main__":
    main()
