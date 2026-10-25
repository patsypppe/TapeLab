import psycopg
import pytest

from tapelab.migrate import apply_migrations


def test_creates_prices_and_is_idempotent(conn):
    assert apply_migrations(conn) == [
        "001_create_prices.sql", "002_create_filings.sql", "003_create_filing_scores.sql",
        "004_create_decisions.sql"]
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


FILING = ("INSERT INTO filings (ticker, cik, form, accession, filed_at, url) "
          "VALUES ('AAPL', 320193, '10-K', %s, '2025-10-31', 'https://example.com/f') RETURNING id")


def test_filings_reject_duplicate_accession(conn):
    apply_migrations(conn)
    conn.execute(FILING, ("0000320193-25-000001",))
    with pytest.raises(psycopg.errors.UniqueViolation):  # same SEC filing twice
        conn.execute(FILING, ("0000320193-25-000001",))


def test_chunks_need_a_filing_and_a_valid_kind_and_go_with_it(conn):
    apply_migrations(conn)
    filing_id = conn.execute(FILING, ("0000320193-25-000001",)).fetchone()[0]
    conn.execute("INSERT INTO filing_chunks (filing_id, idx, kind, text) VALUES (%s, 0, 'table', 'x')",
                 (filing_id,))
    conn.commit()
    with pytest.raises(psycopg.errors.CheckViolation):  # kind must be text or table
        conn.execute("INSERT INTO filing_chunks (filing_id, idx, kind, text) VALUES (%s, 1, 'image', 'x')",
                     (filing_id,))
    conn.rollback()
    with pytest.raises(psycopg.errors.ForeignKeyViolation):  # no such filing
        conn.execute("INSERT INTO filing_chunks (filing_id, idx, kind, text) VALUES (999999, 0, 'text', 'x')")
    conn.rollback()
    conn.execute("DELETE FROM filings WHERE id = %s", (filing_id,))
    assert conn.execute("SELECT count(*) FROM filing_chunks").fetchone()[0] == 0  # chunks deleted too


def test_filing_scores_are_one_per_model_and_within_range(conn):
    apply_migrations(conn)
    filing_id = conn.execute(FILING, ("0000320193-25-000001",)).fetchone()[0]
    insert = "INSERT INTO filing_scores (filing_id, model, score, rationale) VALUES (%s, %s, %s, 'r')"
    conn.execute(insert, (filing_id, "m1", 0.5))
    conn.execute(insert, (filing_id, "m2", -0.5))  # another model may score the same filing
    conn.commit()
    with pytest.raises(psycopg.errors.UniqueViolation):  # same filing and model twice
        conn.execute(insert, (filing_id, "m1", 0.1))
    conn.rollback()
    with pytest.raises(psycopg.errors.CheckViolation):  # score must be between -1 and 1
        conn.execute(insert, (filing_id, "m3", 1.5))


DECISION = ("INSERT INTO decisions (ticker, decided_for, position, reasons) "
            "VALUES ('AAPL', '2025-11-03', %s, '[{\"analyst\": \"technical\", \"score\": 0.3}]')")


def test_decisions_store_reasons_and_one_per_ticker_per_day(conn):
    apply_migrations(conn)
    conn.execute(DECISION, (1,))
    conn.commit()
    reasons = conn.execute("SELECT reasons FROM decisions").fetchone()[0]
    assert reasons[0]["analyst"] == "technical"  # stored as real JSON, not text
    with pytest.raises(psycopg.errors.UniqueViolation):  # the day cannot be redone
        conn.execute(DECISION, (0,))
    conn.rollback()
    with pytest.raises(psycopg.errors.CheckViolation):  # position must be between 0 and 1
        conn.execute("INSERT INTO decisions (ticker, decided_for, position, reasons) "
                     "VALUES ('MSFT', '2025-11-03', 1.5, '[]')")


def test_decisions_cannot_be_changed_or_removed(conn):
    apply_migrations(conn)
    conn.execute(DECISION, (1,))
    conn.commit()
    for statement in ("UPDATE decisions SET position = 0", "DELETE FROM decisions",
                      "TRUNCATE decisions"):
        with pytest.raises(psycopg.errors.RaiseException):
            conn.execute(statement)
        conn.rollback()
    assert conn.execute("SELECT position FROM decisions").fetchone()[0] == 1
