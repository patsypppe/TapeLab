from datetime import date
from decimal import Decimal

import httpx
import pytest

from tapelab.prices import (
    PriceRow,
    closes_through,
    fetch_prices,
    has_price_on,
    latest_price_date,
    parse_yahoo_chart,
    save_prices,
)

# Made-up data in the shape of Yahoo's chart response, not a real download.
# Three days: a normal bar, a day with no data, and a normal bar. The first bar is scaled by 0.5,
# as if a 2-for-1 split happened later.
PAYLOAD = {"chart": {"error": None, "result": [{
    "meta": {"gmtoffset": -18000},
    "timestamp": [1735828200, 1735914600, 1736173800],
    "indicators": {
        "quote": [{
            "open": [100.0, None, 104.0], "high": [110.0, None, 108.0],
            "low": [99.0, None, 103.0], "close": [105.0, None, 106.0],
            "volume": [1000, None, 2000],
        }],
        "adjclose": [{"adjclose": [52.5, None, 106.0]}],
    },
}]}}


def test_parse_adjusts_prices_and_skips_empty_days():
    rows = parse_yahoo_chart("aapl", PAYLOAD)
    assert rows == [
        PriceRow("AAPL", date(2025, 1, 2), Decimal(50), Decimal(55), Decimal("49.5"),
                 Decimal("52.5"), 1000),
        PriceRow("AAPL", date(2025, 1, 6), Decimal(104), Decimal(108), Decimal(103),
                 Decimal(106), 2000),
    ]


def test_parse_raises_on_yahoo_error():
    bad = {"chart": {"error": {"code": "Not Found"}, "result": None}}
    with pytest.raises(ValueError):
        parse_yahoo_chart("ZZZZ", bad)


def test_fetch_sends_ticker_dates_and_user_agent():
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=PAYLOAD)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    rows = fetch_prices("aapl", date(2025, 1, 1), date(2025, 1, 10), client)
    assert len(rows) == 2
    req = seen[0]
    assert req.url.path.endswith("/AAPL") and req.headers["user-agent"].startswith("tapelab")
    assert req.url.params["period1"] == "1735689600" and req.url.params["interval"] == "1d"


def test_save_replaces_existing_day(conn):
    rows = parse_yahoo_chart("AAPL", PAYLOAD)
    assert save_prices(conn, rows) == 2
    revised = [PriceRow("AAPL", date(2025, 1, 2), Decimal(1), Decimal(3), Decimal(1),
                        Decimal(2), 5)]
    save_prices(conn, revised)
    assert conn.execute("SELECT count(*) FROM prices").fetchone()[0] == 2
    assert conn.execute(
        "SELECT close, volume FROM prices WHERE date = '2025-01-02'").fetchone() == (Decimal(2), 5)


def seed(conn):
    rows = [PriceRow("AAPL", date(2025, 1, d), Decimal(d), Decimal(d), Decimal(d), Decimal(d * 10), 1)
            for d in (2, 3, 6, 7)]
    save_prices(conn, rows)


def test_closes_through_returns_oldest_first_and_never_looks_past_the_date(conn):
    seed(conn)
    assert closes_through(conn, "aapl", date(2025, 1, 6)) == [20.0, 30.0, 60.0]
    assert closes_through(conn, "AAPL", date(2025, 1, 6), limit=2) == [30.0, 60.0]
    assert closes_through(conn, "AAPL", date(2025, 1, 1)) == []
    assert closes_through(conn, "MSFT", date(2025, 1, 7)) == []


def test_latest_price_date_and_has_price_on(conn):
    seed(conn)
    assert latest_price_date(conn, "AAPL") == date(2025, 1, 7)
    assert latest_price_date(conn, "MSFT") is None
    assert has_price_on(conn, "AAPL", date(2025, 1, 6)) is True
    assert has_price_on(conn, "AAPL", date(2025, 1, 4)) is False  # a Saturday: no row
