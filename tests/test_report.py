from datetime import date, timedelta
from decimal import Decimal

import pytest

from tapelab.prices import PriceRow, save_prices
from tradeval.compare import Result
from tradeval.report import build_report, format_table, load_history, parse_windows
from tradeval.rules import TrendRule

START = date(2024, 1, 1)


def seed(conn, ticker: str, closes: list[float]) -> None:
    save_prices(conn, [PriceRow(ticker, START + timedelta(days=i), *[Decimal(str(c))] * 4, 1)
                       for i, c in enumerate(closes)])


def test_parse_windows_builds_rules_and_rejects_bad_pairs():
    assert parse_windows(["10/30", "50/200"]) == [TrendRule(10, 30), TrendRule(50, 200)]
    for bad in ("30/10", "20/20", "0/5"):
        with pytest.raises(ValueError):
            parse_windows([bad])


def test_format_table_shows_signs_and_percentages():
    text = format_table([Result("SMA 10/30", 0.1234, 1.5, 2.25, 0.2, 4, 0.5)])
    row = text.splitlines()[1]
    assert "+12.3%" in row and "-20.0%" in row and "50%" in row and "4" in row


def test_load_history_returns_dates_and_closes_oldest_first(conn):
    seed(conn, "AAPL", [10.0, 11.0, 12.0])
    dates, closes = load_history(conn, "aapl")
    assert dates == [START, START + timedelta(days=1), START + timedelta(days=2)]
    assert closes == [10.0, 11.0, 12.0]


def test_report_covers_each_ticker_and_explains_missing_or_short_ones(conn):
    seed(conn, "AAPL", [100.0 + i for i in range(120)])
    seed(conn, "TINY", [100.0 + i for i in range(40)])
    text = build_report(conn, ["AAPL", "TINY", "ZZZZ"], [TrendRule(5, 20), TrendRule(10, 30)], 5.0)
    assert "AAPL: 2024-01-01 to" in text and "120 days" in text
    assert "buy and hold" in text and "SMA 5/20" in text and "SMA 10/30" in text
    assert "TINY: only 40 days of prices, need at least 61" in text
    assert "ZZZZ: no prices loaded" in text
    assert "Variants tried: 2 rules on 1 ticker = 2 runs" in text  # TINY and ZZZZ were not run
