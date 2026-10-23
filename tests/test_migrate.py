import os
import uuid

import psycopg
import pytest

from tapelab.migrate import DEFAULT_URL, apply_migrations

URL = os.environ.get("DATABASE_URL", DEFAULT_URL)


@pytest.fixture
def conn():
    """A connection inside a throwaway schema, so tests never touch real tables."""
    try:
        c = psycopg.connect(URL)
    except psycopg.OperationalError:
        pytest.skip("Postgres is not running (docker compose up -d)")
    schema = f"test_{uuid.uuid4().hex[:8]}"
    c.execute(f"CREATE SCHEMA {schema}")
    c.execute(f"SET search_path TO {schema}")
    c.commit()
    yield c
    c.rollback()
    c.execute(f"DROP SCHEMA {schema} CASCADE")
    c.commit()
    c.close()


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
