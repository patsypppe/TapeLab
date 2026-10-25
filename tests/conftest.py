import os
import uuid
from pathlib import Path

import psycopg
import pytest

from tapelab.db import DEFAULT_URL

URL = os.environ.get("DATABASE_URL", DEFAULT_URL)
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "backend" / "src" / "main" / "resources" / "db" / "migration"


def apply_schema(c: psycopg.Connection) -> None:
    """Run the backend's Flyway files (V1__..., V2__...) in version order."""
    for path in sorted(SCHEMA_DIR.glob("V*.sql"), key=lambda f: int(f.name[1:].split("__")[0])):
        c.execute(path.read_text())


@pytest.fixture
def conn():
    """A connection inside a throwaway schema built from the real migration files."""
    try:
        c = psycopg.connect(URL)
    except psycopg.OperationalError:
        pytest.skip("Postgres is not running (docker compose up -d)")
    schema = f"test_{uuid.uuid4().hex[:8]}"
    c.execute(f"CREATE SCHEMA {schema}")
    c.execute(f"SET search_path TO {schema}")
    apply_schema(c)
    c.commit()
    yield c
    c.rollback()
    c.execute(f"DROP SCHEMA {schema} CASCADE")
    c.commit()
    c.close()
