# TapeLab

Two linked components in one repo.

**Filings RAG** is a research assistant over SEC filings: table-aware chunking, hybrid retrieval
(BM25 + dense, rank fusion), multi-agent analysis. Storage: Postgres (pgvector for embeddings, plus runs and market data).

**TradeEval** is an independent evaluation of the [TradingAgents](https://github.com/TauricResearch/TradingAgents)
multi-agent framework. Upstream already ships a backtester and point-in-time handling, so this
project contributes:
1. Ablations: debate rounds (0/1/3), with/without risk team, single-agent baseline, quick vs deep model tiers
2. Cost and latency per decision for each config (tokens, $, seconds)
3. An independent look-ahead leakage audit of the data each agent sees
4. Alpha, Sharpe and drawdown vs buy-and-hold with confidence intervals, not point estimates
5. TapeLab's retrieval feeding TradingAgents' fundamentals analyst, compared against its default tools

## Status
- [x] Chunker, BM25 + RRF, EDGAR client, FastAPI skeleton, CI
- [x] tradeval: Sharpe, max drawdown, alpha, ablation grid, leakage + entry-date checks
- [ ] Ingestion: EDGAR -> chunks -> Postgres (pgvector) (embeddings + reranker)
- [ ] FinanceBench retrieval ablations
- [ ] Run TradingAgents over a ticker x date grid per config; store runs in Postgres
- [ ] Analysis notebook + write-up; dashboard; AWS deploy (Terraform)

## Results
Fill in only what you measure.

## Dev
    python -m venv .venv && .venv/bin/pip install -e ".[dev]" && .venv/bin/pytest
