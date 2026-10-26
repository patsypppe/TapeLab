# TapeLab

[![ci](https://github.com/patsypppe/TapeLab/actions/workflows/ci.yml/badge.svg)](https://github.com/patsypppe/TapeLab/actions/workflows/ci.yml)

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

## Run order
The backend owns the database schema (Flyway migrations in `backend/src/main/resources/db/migration`), so start it first:

    docker compose up -d                 # Postgres on localhost:5434
    cd backend && ./mvnw spring-boot:run # creates the tables on first start, then serves on :8081
    python -m tapelab.prices AAPL MSFT NVDA --start 2023-01-01
    python -m tapelab.filings AAPL MSFT NVDA
    python -m tapelab.score AAPL MSFT NVDA    # scores each latest 10-K with Gemini (cached)
    python -m tapelab.decide AAPL MSFT NVDA   # saves one insert-only decision per ticker per day
    python -m tapelab.predict AAPL MSFT NVDA  # saves a 10-day price range per ticker (insert-only)
    python -m tradeval.report AAPL MSFT NVDA  # replays trend rules against buy-and-hold on stored prices
    python -m tradeval.forecast_eval AAPL MSFT NVDA  # checks how well the 10-day forecast ranges were calibrated

## See it in the browser
With the backend running (`cd backend && ./mvnw spring-boot:run`), in a second terminal:

    cd frontend && npm install && npm run dev    # open http://localhost:5173

It shows the saved decisions with their reasons, a price chart with the 10-day forecast range, and a
**Predict a date range** panel: pick two dates and it predicts each day's price from only the data before the
range, then shows the actual price, the difference and the error where the dates have already happened.

## Quickstart
    .venv/bin/python -m tapelab.demo   # offline end-to-end run on SYNTHETIC prices; not evidence of performance

## Live Gemini check
    cp .env.example .env   # add GEMINI_API_KEY; .env is git-ignored
    .venv/bin/python -m tapelab.check_gemini

## Status
- [x] Offline agent skeleton: technical + filings-backed fundamentals analysts -> trader -> backtest vs buy-and-hold
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
