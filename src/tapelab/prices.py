"""Downloads daily prices from Yahoo's public chart endpoint and saves them into Postgres."""
import argparse
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import httpx
import psycopg

from .db import connect

CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
USER_AGENT = "tapelab-research (personal project)"


@dataclass(frozen=True)
class PriceRow:
    ticker: str
    date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


def _money(x: float) -> Decimal:
    return Decimal(str(round(x, 4)))


def parse_yahoo_chart(ticker: str, payload: dict) -> list[PriceRow]:
    """Turn Yahoo's JSON into price rows adjusted for splits and dividends; skip days with no data."""
    error = payload["chart"]["error"]
    if error:
        raise ValueError(f"Yahoo returned an error for {ticker}: {error}")
    result = payload["chart"]["result"][0]
    offset = result["meta"].get("gmtoffset", 0)
    quote = result["indicators"]["quote"][0]
    adjclose = result["indicators"]["adjclose"][0]["adjclose"]
    rows = []
    for i, ts in enumerate(result["timestamp"]):
        o, h, lo, c, v, adj = (quote["open"][i], quote["high"][i], quote["low"][i],
                               quote["close"][i], quote["volume"][i], adjclose[i])
        if None in (o, h, lo, c, v, adj):
            continue
        factor = adj / c  # scales the whole bar so a split does not look like a crash
        day = datetime.fromtimestamp(ts + offset, tz=UTC).date()
        rows.append(PriceRow(ticker.upper(), day, _money(o * factor), _money(h * factor),
                             _money(lo * factor), _money(c * factor), int(v)))
    return rows


def fetch_prices(ticker: str, start: date, end: date, client: httpx.Client) -> list[PriceRow]:
    """Download one ticker's daily bars from start up to (not including) end."""
    def to_unix(d: date) -> int:
        return int(datetime(d.year, d.month, d.day, tzinfo=UTC).timestamp())

    response = client.get(
        CHART_URL.format(ticker=ticker.upper()),
        params={"period1": to_unix(start), "period2": to_unix(end), "interval": "1d",
                "events": "div,splits"},
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return parse_yahoo_chart(ticker, response.json())


def save_prices(conn: psycopg.Connection, rows: list[PriceRow]) -> int:
    """Insert rows, replacing any existing row for the same ticker and day; returns rows written."""
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO prices (ticker, date, open, high, low, close, volume) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s) "
            "ON CONFLICT (ticker, date) DO UPDATE SET open = EXCLUDED.open, "
            "high = EXCLUDED.high, low = EXCLUDED.low, close = EXCLUDED.close, "
            "volume = EXCLUDED.volume",
            [(r.ticker, r.date, r.open, r.high, r.low, r.close, r.volume) for r in rows],
        )
    conn.commit()
    return len(rows)


def closes_through(conn: psycopg.Connection, ticker: str, as_of: date, limit: int = 60) -> list[float]:
    """The last `limit` closing prices on or before as_of, oldest first, never anything later."""
    rows = conn.execute(
        "SELECT close FROM prices WHERE ticker = %s AND date <= %s ORDER BY date DESC LIMIT %s",
        (ticker.upper(), as_of, limit),
    ).fetchall()
    return [float(r[0]) for r in reversed(rows)]


def latest_price_date(conn: psycopg.Connection, ticker: str) -> date | None:
    """The most recent day we hold a price for, or None if the ticker has no prices."""
    return conn.execute("SELECT max(date) FROM prices WHERE ticker = %s", (ticker.upper(),)).fetchone()[0]


def has_price_on(conn: psycopg.Connection, ticker: str, day: date) -> bool:
    """True if there is a price row for this ticker on exactly this day (so it was a trading day)."""
    return conn.execute(
        "SELECT 1 FROM prices WHERE ticker = %s AND date = %s", (ticker.upper(), day)).fetchone() is not None


def main() -> None:
    """Command-line entry point: python -m tapelab.prices AAPL MSFT --start 2020-01-01."""
    parser = argparse.ArgumentParser(description="Load daily prices into Postgres")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--start", type=date.fromisoformat, default=date.today() - timedelta(days=365))
    args = parser.parse_args()
    today = date.today()  # today's bar may be unfinished, so it is left out
    with httpx.Client(timeout=30) as client, connect() as conn:
        for ticker in args.tickers:
            rows = [r for r in fetch_prices(ticker, args.start, today, client) if r.date < today]
            print(f"{ticker.upper()}: saved {save_prices(conn, rows)} rows")


if __name__ == "__main__":
    main()
