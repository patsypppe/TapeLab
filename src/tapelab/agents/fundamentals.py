from datetime import date

import psycopg

from ..chunking import chunk_filing
from ..retrieval import bm25_rank, rrf
from .llm import LLM
from .types import Signal

QUESTION = "revenue growth net income margin outlook risk"


def fundamentals_signal(filing_text: str, llm: LLM, source: str = "10-K") -> Signal:
    """Retrieve the most relevant filing passages and have the LLM score them."""
    chunks = chunk_filing(filing_text, source)
    if not chunks:
        return Signal("fundamentals", 0.0, "no filing available")
    texts = [c.text for c in chunks]
    top = rrf([bm25_rank(QUESTION, texts)])[:3]
    evidence = [texts[i] for i in top]
    score, why = llm.score_fundamentals(evidence)
    return Signal("fundamentals", score, why)


def latest_filing_before(conn: psycopg.Connection, ticker: str, as_of: date,
                         form: str = "10-K") -> tuple[int, date] | None:
    """The newest filing of this form filed strictly before as_of, so the agent never sees the future.

    Strictly before, not on the day: a filing released after the close on as_of was not
    available to a decision made at that day's close.
    """
    row = conn.execute(
        "SELECT id, filed_at FROM filings WHERE ticker = %s AND form = %s AND filed_at < %s "
        "ORDER BY filed_at DESC LIMIT 1",
        (ticker.upper(), form, as_of),
    ).fetchone()
    return None if row is None else (row[0], row[1])


def score_filing(conn: psycopg.Connection, llm: LLM, filing_id: int, top_k: int = 5) -> Signal:
    """Score a stored filing, reusing the saved score for this model if there is one."""
    model = getattr(llm, "model", None) or type(llm).__name__
    cached = conn.execute(
        "SELECT score, rationale FROM filing_scores WHERE filing_id = %s AND model = %s",
        (filing_id, model),
    ).fetchone()
    if cached:
        return Signal("fundamentals", cached[0], cached[1])
    texts = [r[0] for r in conn.execute(
        "SELECT text FROM filing_chunks WHERE filing_id = %s ORDER BY idx", (filing_id,))]
    if not texts:
        return Signal("fundamentals", 0.0, "filing has no text")
    top = rrf([bm25_rank(QUESTION, texts)])[:top_k]
    score, why = llm.score_fundamentals([texts[i] for i in top])
    conn.execute(
        "INSERT INTO filing_scores (filing_id, model, score, rationale) VALUES (%s, %s, %s, %s) "
        "ON CONFLICT (filing_id, model) DO NOTHING",
        (filing_id, model, score, why),
    )
    conn.commit()
    return Signal("fundamentals", score, why)
