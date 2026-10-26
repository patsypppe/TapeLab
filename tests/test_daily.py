from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import pytest

from tapelab.daily import STALE_AFTER_DAYS, exit_code, format_summary, last_complete_day, run_daily
from tapelab.prices import PriceRow

# 5pm in New York on Friday 2026-10-23 (daylight time, UTC-4), after the close
AFTER_CLOSE = datetime(2026, 10, 23, 21, 0, tzinfo=UTC)
FRIDAY = date(2026, 10, 23)


class FakeLLM:
    model = "fake"

    def score_fundamentals(self, evidence):
        return 0.4, "fine"


def no_filing(conn, ticker):
    return "unchanged", "no 10-K found"


def prices_through(last: date, base: float = 100.0):
    """A fetcher that serves one price per calendar day, rising slowly, up to `last` (and never past the request)."""
    def fetch(ticker, start, end):
        days = (end - start).days
        out = []
        for i in range(days):
            day = start + timedelta(days=i)
            if day <= last:
                value = Decimal(str(round(base + (day - date(2025, 1, 1)).days * 0.1, 4)))
                out.append(PriceRow(ticker, day, value, value, value, value, 1000))
        return out
    return fetch


def run(conn, tickers, fetch, now=AFTER_CLOSE, get_llm=FakeLLM, filing=no_filing):
    return run_daily(conn, tickers, fetch, filing, get_llm, now)


def status_of(results, ticker, step):
    return next(r.status for r in results if r.ticker == ticker and r.step == step)


def count(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_a_price_bar_counts_as_final_only_after_4_30pm_new_york_time():
    assert last_complete_day(datetime(2026, 10, 23, 20, 29, tzinfo=UTC)) == date(2026, 10, 22)  # 4:29pm
    assert last_complete_day(datetime(2026, 10, 23, 20, 30, tzinfo=UTC)) == FRIDAY  # 4:30pm
    assert last_complete_day(datetime(2026, 10, 23, 13, 0, tzinfo=UTC)) == date(2026, 10, 22)  # morning


def test_the_first_run_loads_prices_then_decides_and_forecasts(conn):
    results = run(conn, ["aapl"], prices_through(FRIDAY))
    assert [(r.step, r.status) for r in results] == [
        ("prices", "done"), ("filing", "unchanged"), ("decision", "done"), ("forecast", "done")]
    assert count(conn, "decisions") == 1 and count(conn, "forecasts") == 1
    assert conn.execute("SELECT max(date) FROM prices").fetchone()[0] == FRIDAY
    assert exit_code(results) == 0


def test_running_it_again_changes_nothing_and_reports_unchanged(conn):
    run(conn, ["AAPL"], prices_through(FRIDAY))
    before = (count(conn, "prices"), count(conn, "decisions"), count(conn, "forecasts"))
    results = run(conn, ["AAPL"], prices_through(FRIDAY))
    assert [r.status for r in results] == ["unchanged"] * 4
    assert (count(conn, "prices"), count(conn, "decisions"), count(conn, "forecasts")) == before


def test_a_new_day_of_prices_produces_a_new_decision_and_forecast(conn):
    run(conn, ["AAPL"], prices_through(FRIDAY - timedelta(days=1)), now=AFTER_CLOSE - timedelta(days=1))
    results = run(conn, ["AAPL"], prices_through(FRIDAY))
    assert status_of(results, "AAPL", "prices") == "done"
    assert status_of(results, "AAPL", "decision") == "done" and status_of(results, "AAPL", "forecast") == "done"
    assert count(conn, "decisions") == 2 and count(conn, "forecasts") == 2


def test_one_tickers_failure_does_not_stop_another_and_makes_the_exit_code_one(conn):
    good = prices_through(FRIDAY)

    def fetch(ticker, start, end):
        if ticker == "BAD":
            raise RuntimeError("Yahoo is down")
        return good(ticker, start, end)

    results = run(conn, ["BAD", "GOOD"], fetch)
    assert status_of(results, "BAD", "prices") == "failed"
    assert status_of(results, "BAD", "decision") == "skipped" and status_of(results, "BAD", "forecast") == "skipped"
    assert status_of(results, "GOOD", "decision") == "done"
    assert exit_code(results) == 1
    assert "Yahoo is down" in next(r.detail for r in results if r.status == "failed")
    assert count(conn, "decisions") == 1  # the connection is still usable after the failure


def test_a_failed_download_still_decides_from_the_prices_already_stored(conn):
    run(conn, ["AAPL"], prices_through(FRIDAY - timedelta(days=1)), now=AFTER_CLOSE - timedelta(days=1))

    def broken(ticker, start, end):
        raise RuntimeError("timeout")

    results = run(conn, ["AAPL"], broken)
    assert status_of(results, "AAPL", "prices") == "failed"
    assert status_of(results, "AAPL", "decision") == "unchanged"  # already decided for the stored latest day


def test_prices_that_stopped_arriving_raise_a_warning_but_not_a_failure(conn):
    old = FRIDAY - timedelta(days=STALE_AFTER_DAYS + 3)
    run(conn, ["AAPL"], prices_through(old), now=AFTER_CLOSE - timedelta(days=STALE_AFTER_DAYS + 3))
    results = run(conn, ["AAPL"], prices_through(old))  # nothing newer is available
    warning = next(r for r in results if r.status == "warning")
    assert "may have stopped updating" in warning.detail
    assert exit_code(results) == 0


def test_a_missing_gemini_key_fails_the_decision_but_not_the_forecast(conn):
    def no_key():
        raise RuntimeError("GEMINI_API_KEY is not set")

    results = run(conn, ["AAPL"], prices_through(FRIDAY), get_llm=no_key)
    assert status_of(results, "AAPL", "decision") == "failed"
    assert status_of(results, "AAPL", "forecast") == "done"
    assert count(conn, "decisions") == 0


def test_the_summary_lists_each_ticker_and_counts_outcomes(conn):
    text = format_summary(run(conn, ["AAPL", "MSFT"], prices_through(FRIDAY)))
    assert "AAPL" in text and "MSFT" in text and "decision" in text
    assert "6 done" in text and "2 unchanged" in text


@pytest.mark.parametrize("hour,expected", [(13, date(2026, 10, 22)), (22, FRIDAY)])
def test_running_before_the_close_never_records_todays_unfinished_bar(conn, hour, expected):
    run(conn, ["AAPL"], prices_through(FRIDAY), now=datetime(2026, 10, 23, hour, 0, tzinfo=UTC))
    assert conn.execute("SELECT max(date) FROM prices").fetchone()[0] == expected
