"""Hybrid retrieval: BM25 and vector rankings fused with reciprocal rank fusion."""
import math
import re
from collections import Counter


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9$%.]+", text.lower())


def bm25_rank(query: str, docs: list[str], k1: float = 1.5, b: float = 0.75) -> list[int]:
    toks = [tokenize(d) for d in docs]
    avg = sum(map(len, toks)) / max(len(toks), 1) or 1.0
    df: Counter[str] = Counter()
    for t in toks:
        df.update(set(t))
    n = len(docs)
    scores = []
    for i, t in enumerate(toks):
        tf = Counter(t)
        s = 0.0
        for q in tokenize(query):
            if q not in tf:
                continue
            idf = math.log(1 + (n - df[q] + 0.5) / (df[q] + 0.5))
            s += idf * tf[q] * (k1 + 1) / (tf[q] + k1 * (1 - b + b * len(t) / avg))
        scores.append(s)
    return sorted(range(n), key=lambda i: scores[i], reverse=True)


def rrf(rankings: list[list[int]], k: int = 60) -> list[int]:
    """Reciprocal rank fusion over several ranked lists of doc ids."""
    fused: Counter[int] = Counter()
    for ranking in rankings:
        for rank, doc in enumerate(ranking):
            fused[doc] += 1 / (k + rank + 1)
    return [doc for doc, _ in fused.most_common()]
