import os
import uuid

import psycopg
import pytest

from tapelab.migrate import DEFAULT_URL

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
