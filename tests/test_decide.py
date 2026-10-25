from datetime import date, timedelta
from decimal import Decimal

import pytest

from tapelab.chunking import Chunk
from tapelab.decide import make_decision
from tapelab.edgar import FilingRef
from tapelab.filings import save_filing
from tapelab.prices import PriceRow, save_prices

START = date(2025, 1, 1)


class FakeLLM:
    model = "fake"

    def __init__(self, score: float):
        self.score = score

    def score_fundamentals(self, evidence: list[str]) -> tuple[float, str]:
        return self.score, "fake reason"


def seed_prices(conn, closes: list[float]) -> date:
    """One price row per consecutive day; returns the last day."""
    rows = [PriceRow("AAPL", START + timedelta(days=i), Decimal(str(c)), Decimal(str(c)),
                     Decimal(str(c)), Decimal(str(c)), 1) for i, c in enumerate(closes)]
    save_prices(conn, rows)
    return rows[-1].date


def seed_filing(conn, filed: date) -> None:
    ref = FilingRef("AAPL", 320193, "10-K", "a-1", filed, None, None, "https://example.com")
    save_filing(conn, ref, [Chunk("Revenue growth and net income margin outlook", "text", "s", 0)])


RISING = [100 + i for i in range(60)]
FALLING = [160 - i for i in range(60)]


def saved_rows(conn):
    return conn.execute("SELECT count(*) FROM decisions").fetchone()[0]


def test_rising_prices_and_good_filing_give_a_long_decision_with_reasons_saved(conn):
    last = seed_prices(conn, RISING)
    seed_filing(conn, START - timedelta(days=1))
    result = make_decision(conn, FakeLLM(0.4), "aapl", last)
    assert result.created and result.position == 1.0
    assert [s.analyst for s in result.signals] == ["technical", "fundamentals"]
    row = conn.execute("SELECT position, reasons, config, filing_id FROM decisions").fetchone()
    assert row[0] == Decimal("1.000") and row[3] == result.filing_id
    assert [r["analyst"] for r in row[1]] == ["technical", "fundamentals"]
    assert row[2]["model"] == "fake" and row[2]["technical"] == {"fast": 10, "slow": 30}


def test_falling_prices_and_bad_filing_give_a_flat_decision(conn):
    last = seed_prices(conn, FALLING)
    seed_filing(conn, START - timedelta(days=1))
    assert make_decision(conn, FakeLLM(-0.9), "AAPL", last).position == 0.0


def test_a_day_cannot_be_redone_and_the_saved_decision_is_returned(conn):
    last = seed_prices(conn, RISING)
    first = make_decision(conn, FakeLLM(0.4), "AAPL", last)
    again = make_decision(conn, FakeLLM(-1.0), "AAPL", last)
    assert first.created and not again.created
    assert again.position == first.position and again.signals == first.signals
    assert saved_rows(conn) == 1


def test_without_a_filing_only_the_technical_signal_is_used(conn):
    last = seed_prices(conn, RISING)
    result = make_decision(conn, FakeLLM(0.4), "AAPL", last)
    assert [s.analyst for s in result.signals] == ["technical"] and result.filing_id is None


def test_a_filing_released_on_the_decision_day_is_not_used(conn):
    last = seed_prices(conn, RISING)
    seed_filing(conn, last)  # filed the same day: not known at that day's close
    assert make_decision(conn, FakeLLM(0.4), "AAPL", last).filing_id is None


def test_a_day_without_a_price_is_rejected(conn):
    seed_prices(conn, RISING)
    with pytest.raises(ValueError):
        make_decision(conn, FakeLLM(0.4), "AAPL", START - timedelta(days=5))
    assert saved_rows(conn) == 0
