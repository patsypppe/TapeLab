from datetime import date

import httpx

from tapelab.chunking import Chunk
from tapelab.edgar import FilingRef
from tapelab.filings import load_filing, save_filing

REF = FilingRef("AAPL", 320193, "10-K", "0000320193-25-000079", date(2025, 10, 31), None,
                date(2025, 9, 27), "https://www.sec.gov/Archives/edgar/data/320193/x/a.htm")

# Made-up filing HTML: one paragraph and one table.
HTML = ("<p>Revenue increased 12%.</p>"
        "<table><tr><td>Year</td><td>Revenue</td></tr><tr><td>2024</td><td>112</td></tr></table>")


def count(conn, table):
    return conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]


def test_save_filing_stores_chunks_and_ignores_a_repeat(conn):
    chunks = [Chunk("hello", "text", "s", 0), Chunk("| a | b |", "table", "s", 1)]
    assert save_filing(conn, REF, chunks) is True
    assert save_filing(conn, REF, chunks) is False  # same accession: nothing added
    assert count(conn, "filings") == 1 and count(conn, "filing_chunks") == 2
    assert conn.execute("SELECT filed_at FROM filings").fetchone()[0] == date(2025, 10, 31)


def test_load_filing_downloads_once_and_keeps_the_table_whole(conn):
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, text=HTML)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    chunks = load_filing(conn, client, REF)
    assert [c.kind for c in chunks] == ["text", "table"]
    assert conn.execute("SELECT text FROM filing_chunks WHERE kind = 'table'").fetchone()[0] == (
        "| Year | Revenue |\n| 2024 | 112 |")
    assert load_filing(conn, client, REF) is None  # already saved
    assert len(requests) == 1  # the second call did not download again
