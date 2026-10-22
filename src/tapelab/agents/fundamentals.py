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
