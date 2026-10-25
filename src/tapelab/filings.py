"""Downloads SEC filings, splits them into chunks and saves both into Postgres."""
import argparse

import httpx
import psycopg

from .chunking import Chunk, chunk_filing
from .db import connect
from .edgar import FilingRef, fetch_document, list_filings, sec_client
from .html_text import html_to_text


def is_saved(conn: psycopg.Connection, accession: str) -> bool:
    """True if this filing is already in the database."""
    return conn.execute("SELECT 1 FROM filings WHERE accession = %s", (accession,)).fetchone() is not None


def save_filing(conn: psycopg.Connection, ref: FilingRef, chunks: list[Chunk]) -> bool:
    """Save a filing and its chunks together; returns False if the filing was already stored."""
    row = conn.execute(
        "INSERT INTO filings (ticker, cik, form, accession, filed_at, accepted_at, period_end, url) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (accession) DO NOTHING RETURNING id",
        (ref.ticker, ref.cik, ref.form, ref.accession, ref.filed_at, ref.accepted_at,
         ref.period_end, ref.url),
    ).fetchone()
    if row is None:
        return False
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO filing_chunks (filing_id, idx, kind, text) VALUES (%s, %s, %s, %s)",
            [(row[0], c.index, c.kind, c.text) for c in chunks],
        )
    conn.commit()
    return True


def load_filing(conn: psycopg.Connection, client: httpx.Client, ref: FilingRef) -> list[Chunk] | None:
    """Download, convert, chunk and save one filing; None means it was already stored."""
    if is_saved(conn, ref.accession):
        return None
    text = html_to_text(fetch_document(client, ref)).replace("\x00", "")  # Postgres rejects NUL
    chunks = chunk_filing(text, ref.accession)
    save_filing(conn, ref, chunks)
    return chunks


def main() -> None:
    """Command-line entry point: python -m tapelab.filings AAPL MSFT --form 10-K --limit 1."""
    parser = argparse.ArgumentParser(description="Load SEC filings into Postgres")
    parser.add_argument("tickers", nargs="+")
    parser.add_argument("--form", default="10-K")
    parser.add_argument("--limit", type=int, default=1, help="newest N filings per ticker")
    args = parser.parse_args()
    with sec_client() as client, connect() as conn:
        for ticker in args.tickers:
            for ref in list_filings(client, ticker, args.form, args.limit):
                chunks = load_filing(conn, client, ref)
                label = f"{ref.ticker} {ref.form} filed {ref.filed_at}"
                if chunks is None:
                    print(f"{label}: already saved")
                else:
                    tables = sum(c.kind == "table" for c in chunks)
                    print(f"{label}: saved {len(chunks)} chunks ({tables} tables)")


if __name__ == "__main__":
    main()
