"""Makes and saves a 10-day forecast range per ticker: python -m tapelab.predict AAPL."""
import argparse
from dataclasses import dataclass
from datetime import date, timedelta

import psycopg
from psycopg.types.json import Jsonb

from .db import connect
from .forecast import HORIZON, MODELS, WINDOW, forecast
from .prices import closes_through, has_price_on, latest_price_date


@dataclass(frozen=True)
class SavedForecast:
    ticker: str
    as_of: date
    model: str
    last_close: float
    points: list[dict]  # day_ahead, date, median, low, high
    created: bool  # False when this ticker, day and model had already been forecast


def next_weekdays(start: date, count: int) -> list[date]:
    """The next `count` weekdays after `start`. Market holidays are not known, so dates can be off by a day."""
    days, day = [], start
    while len(days) < count:
        day += timedelta(days=1)
        if day.weekday() < 5:
            days.append(day)
    return days


def make_forecast(conn: psycopg.Connection, ticker: str, as_of: date, model: str = "random_walk") -> SavedForecast:
    """Forecast from the closes up to as_of and save it once; a repeat returns the saved one."""
    ticker = ticker.upper()
    if not has_price_on(conn, ticker, as_of):
        raise ValueError(f"No {ticker} price on {as_of}; it was not a trading day or is not loaded")
    closes = closes_through(conn, ticker, as_of, WINDOW + 1)
    dates = next_weekdays(as_of, HORIZON)
    points = [{"day_ahead": p.day_ahead, "date": dates[p.day_ahead - 1].isoformat(),
               "median": round(p.median, 4), "low": round(p.low, 4), "high": round(p.high, 4)}
              for p in forecast(closes, HORIZON, WINDOW, model)]
    row = conn.execute(
        "INSERT INTO forecasts (ticker, as_of, model, horizon, last_close, points) "
        "VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (ticker, as_of, model) DO NOTHING RETURNING id",
        (ticker, as_of, model, HORIZON, closes[-1], Jsonb(points)),
    ).fetchone()
    conn.commit()
    if row is not None:
        return SavedForecast(ticker, as_of, model, closes[-1], points, created=True)
    last_close, saved = conn.execute(
        "SELECT last_close, points FROM forecasts WHERE ticker = %s AND as_of = %s AND model = %s",
        (ticker, as_of, model)).fetchone()
    return SavedForecast(ticker, as_of, model, float(last_close), saved, created=False)


def main() -> None:
    """Command-line entry point; prints each ticker's range for the next 10 trading days."""
    parser = argparse.ArgumentParser(description="Make and save a 10-day forecast range for each ticker")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--as-of", type=date.fromisoformat, help="default: the latest day with a price")
    parser.add_argument("--model", choices=MODELS, default="random_walk")
    args = parser.parse_args()
    with connect() as conn:
        for ticker in args.tickers:
            day = args.as_of or latest_price_date(conn, ticker)
            if day is None:
                print(f"{ticker.upper()}: no prices loaded (run python -m tapelab.prices first)")
                continue
            result = make_forecast(conn, ticker, day, args.model)
            note = "saved" if result.created else "already made for this day, showing the saved one"
            print(f"{result.ticker} from the close of {result.as_of} ({result.last_close:.2f}), "
                  f"{result.model}: 80% range ({note})")
            for p in result.points:
                print(f"  +{p['day_ahead']:>2}  {p['date']}  {p['low']:>9.2f}  to  {p['high']:>9.2f}")
    print("\nA range, not a prediction of direction: the middle is simply the last close, "
          "and about one time in five the price is expected outside it.")


if __name__ == "__main__":
    main()
