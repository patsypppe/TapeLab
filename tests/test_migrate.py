import psycopg
import pytest

from tapelab.migrate import apply_migrations


def test_creates_prices_and_is_idempotent(conn):
    assert apply_migrations(conn) == ["001_create_prices.sql"]
    assert apply_migrations(conn) == []  # second run applies nothing
    conn.execute("INSERT INTO prices VALUES ('AAPL', '2025-01-02', 10, 12, 9, 11, 1000)")
    assert conn.execute("SELECT count(*) FROM prices").fetchone()[0] == 1


def test_prices_rejects_bad_rows(conn):
    apply_migrations(conn)
    conn.commit()
    with pytest.raises(psycopg.errors.CheckViolation):  # high below low
        conn.execute("INSERT INTO prices VALUES ('AAPL', '2025-01-02', 10, 8, 9, 11, 1000)")
    conn.rollback()
    conn.execute("INSERT INTO prices VALUES ('AAPL', '2025-01-02', 10, 12, 9, 11, 1000)")
    with pytest.raises(psycopg.errors.UniqueViolation):  # same ticker and date twice
        conn.execute("INSERT INTO prices VALUES ('AAPL', '2025-01-02', 10, 12, 9, 11, 1000)")
