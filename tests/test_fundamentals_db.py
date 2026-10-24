from datetime import date

from tapelab.agents.fundamentals import latest_filing_before, score_filing
from tapelab.chunking import Chunk
from tapelab.edgar import FilingRef
from tapelab.filings import save_filing
from tapelab.migrate import apply_migrations


class FakeLLM:
    """Records what it was asked, so tests can see which passages reached the model."""

    def __init__(self, model: str = "fake"):
        self.model = model
        self.calls: list[list[str]] = []

    def score_fundamentals(self, evidence: list[str]) -> tuple[float, str]:
        self.calls.append(evidence)
        return 0.4, "looks fine"


def ref(accession: str, filed: date) -> FilingRef:
    return FilingRef("AAPL", 320193, "10-K", accession, filed, None, None, "https://example.com")


def store(conn, accession: str, filed: date, texts: list[str]) -> int:
    save_filing(conn, ref(accession, filed), [Chunk(t, "text", "s", i) for i, t in enumerate(texts)])
    return conn.execute("SELECT id FROM filings WHERE accession = %s", (accession,)).fetchone()[0]


def test_latest_filing_is_strictly_before_the_date(conn):
    apply_migrations(conn)
    old = store(conn, "a-1", date(2024, 11, 1), ["x"])
    new = store(conn, "a-2", date(2025, 10, 31), ["x"])
    assert latest_filing_before(conn, "aapl", date(2025, 10, 31)) == (old, date(2024, 11, 1))
    assert latest_filing_before(conn, "AAPL", date(2025, 11, 1)) == (new, date(2025, 10, 31))
    assert latest_filing_before(conn, "AAPL", date(2024, 11, 1)) is None
    assert latest_filing_before(conn, "MSFT", date(2026, 1, 1)) is None


def test_score_sends_relevant_passages_and_is_cached_per_model(conn):
    apply_migrations(conn)
    texts = [f"Unrelated note number {i} about office leases." for i in range(8)]
    texts.append("Revenue growth was strong and net income margin improved this year.")
    filing_id = store(conn, "a-1", date(2025, 10, 31), texts)

    llm = FakeLLM()
    first = score_filing(conn, llm, filing_id, top_k=2)
    assert (first.score, first.rationale) == (0.4, "looks fine")
    assert len(llm.calls) == 1 and len(llm.calls[0]) == 2
    assert "Revenue growth was strong and net income margin improved this year." in llm.calls[0]

    assert score_filing(conn, llm, filing_id, top_k=2) == first
    assert len(llm.calls) == 1  # second call used the saved score

    other = FakeLLM(model="other")
    score_filing(conn, other, filing_id)
    assert len(other.calls) == 1  # a different model is scored separately
    assert conn.execute("SELECT count(*) FROM filing_scores").fetchone()[0] == 2


def test_filing_without_text_gets_neutral_score_and_nothing_saved(conn):
    apply_migrations(conn)
    filing_id = store(conn, "a-1", date(2025, 10, 31), [])
    llm = FakeLLM()
    assert score_filing(conn, llm, filing_id).score == 0.0
    assert llm.calls == []
    assert conn.execute("SELECT count(*) FROM filing_scores").fetchone()[0] == 0
