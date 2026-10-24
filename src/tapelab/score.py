"""Scores each ticker's latest 10-K with the fundamentals analyst: python -m tapelab.score AAPL."""
import argparse
from datetime import date

from .agents.fundamentals import latest_filing_before, score_filing
from .agents.gemini import GeminiLLM
from .agents.llm import RuleBasedLLM
from .migrate import connect


def main() -> None:
    """Command-line entry point; prints one line per ticker."""
    parser = argparse.ArgumentParser(description="Score the latest 10-K for each ticker")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today(),
                        help="only use filings filed before this date (default: today)")
    parser.add_argument("--llm", choices=["gemini", "rule"], default="gemini")
    args = parser.parse_args()
    llm = GeminiLLM() if args.llm == "gemini" else RuleBasedLLM()
    with connect() as conn:
        for ticker in args.tickers:
            found = latest_filing_before(conn, ticker, args.as_of)
            if found is None:
                print(f"{ticker.upper()}: no 10-K filed before {args.as_of}")
                continue
            filing_id, filed_at = found
            signal = score_filing(conn, llm, filing_id)
            print(f"{ticker.upper()} (10-K filed {filed_at}): {signal.score:+.2f}  {signal.rationale}")


if __name__ == "__main__":
    main()
