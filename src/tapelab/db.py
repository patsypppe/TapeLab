"""Database connection helper. The schema itself is owned by the backend's Flyway migrations."""
import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

DEFAULT_URL = "postgresql://tapelab:tapelab@localhost:5434/tapelab"


def connect() -> psycopg.Connection:
    """Open a connection using DATABASE_URL, or the local docker-compose database by default."""
    return psycopg.connect(os.environ.get("DATABASE_URL", DEFAULT_URL))
