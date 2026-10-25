"""Applies the Flyway-named SQL files (V1__..., V2__...) from the backend to Postgres, once each."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = "postgresql://tapelab:tapelab@localhost:5434/tapelab"
MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "backend" / "src" / "main" / "resources" / "db" / "migration"


def connect() -> psycopg.Connection:
    """Open a connection using DATABASE_URL, or the local docker-compose database by default."""
    return psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_URL))


def apply_migrations(conn: psycopg.Connection, directory: Path = MIGRATIONS_DIR) -> list[str]:
    """Run every migration file not yet recorded in schema_migrations; return the ones applied."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
    )
    done = {row[0] for row in conn.execute("SELECT version FROM schema_migrations")}
    applied = []
    for path in sorted(directory.glob("V*.sql"), key=lambda f: int(f.name[1:].split("__")[0])):
        if path.name in done:
            continue
        conn.execute(path.read_text())
        conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
        applied.append(path.name)
    conn.commit()
    return applied


def main() -> None:
    """Command-line entry point: python -m tapelab.migrate."""
    with connect() as conn:
        applied = apply_migrations(conn)
    print("applied:", ", ".join(applied) if applied else "nothing new")


if __name__ == "__main__":
    main()
