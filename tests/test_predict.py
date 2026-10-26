import random
from datetime import date, timedelta
from decimal import Decimal

import pytest

from tapelab.predict import make_forecast, next_weekdays
from tapelab.prices import PriceRow, save_prices

START = date(2025, 1, 1)


def seed_prices(conn, n: int = 100) -> date:
    rng, price, rows = random.Random(3), 100.0, []
    for i in range(n):
        price *= 1 + rng.gauss(0.0004, 0.012)
        rows.append(PriceRow("AAPL", START + timedelta(days=i), *[Decimal(str(round(price, 4)))] * 4, 1))
    save_prices(conn, rows)
    return rows[-1].date


def test_next_weekdays_skips_weekends():
    friday = date(2025, 1, 3)
    assert friday.weekday() == 4
    days = next_weekdays(friday, 3)
    assert days == [date(2025, 1, 6), date(2025, 1, 7), date(2025, 1, 8)]


def test_a_forecast_is_saved_once_with_ten_ordered_ranges(conn):
    last = seed_prices(conn)
    first = make_forecast(conn, "aapl", last)
    assert first.created and len(first.points) == 10
    assert all(p["low"] < p["median"] < p["high"] for p in first.points)
    assert [p["day_ahead"] for p in first.points] == list(range(1, 11))
    assert all(date.fromisoformat(p["date"]) > last for p in first.points)
    stored = conn.execute("SELECT model, horizon, last_close FROM forecasts").fetchone()
    assert stored == ("random_walk", 10, Decimal(str(first.last_close)))

    again = make_forecast(conn, "AAPL", last)
    assert not again.created and again.points == first.points
    assert conn.execute("SELECT count(*) FROM forecasts").fetchone()[0] == 1


def test_a_different_model_is_a_separate_forecast(conn):
    last = seed_prices(conn)
    make_forecast(conn, "AAPL", last, "random_walk")
    assert make_forecast(conn, "AAPL", last, "drift").created
    assert conn.execute("SELECT count(*) FROM forecasts").fetchone()[0] == 2


def test_a_forecast_uses_only_closes_up_to_its_day(conn):
    last = seed_prices(conn, 120)
    earlier = START + timedelta(days=99)  # 20 later closes exist, and must not influence it
    assert make_forecast(conn, "AAPL", earlier).last_close == pytest.approx(
        float(conn.execute("SELECT close FROM prices WHERE ticker = 'AAPL' AND date = %s", (earlier,)).fetchone()[0]))
    assert last > earlier


def test_missing_prices_or_too_little_history_are_rejected(conn):
    last = seed_prices(conn, 100)
    with pytest.raises(ValueError):
        make_forecast(conn, "AAPL", last + timedelta(days=30))  # no price that day
    short = START + timedelta(days=30)  # only 31 closes exist by then
    with pytest.raises(ValueError):
        make_forecast(conn, "AAPL", short)
    assert conn.execute("SELECT count(*) FROM forecasts").fetchone()[0] == 0
