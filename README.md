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

The steps from prices to predict can be done in one go with `python -m tapelab.daily` (see below).

## Every day
One command brings a watchlist up to date: prices, a new 10-K if there is one, the day's decision and the 10-day forecast.

    python -m tapelab.daily AAPL MSFT NVDA          # add --llm rule to skip Gemini

It is safe to run twice (finished work is reported as `unchanged`), one failing step never stops the others, and it
exits 1 if anything failed. It only records a day's price once that day is final (after 4:30pm New York time), so run it
in the evening. A warning means the newest price is more than 4 days old, i.e. the data may have stopped arriving.

To run it on a schedule, use cron (`crontab -e`) with absolute paths, since cron has no shell profile or `.env` loading
beyond what the program does itself. This runs at 5pm US Eastern on weekdays if your Mac is set to Eastern time (cron uses
the machine's local time, so shift the hour otherwise):

    0 17 * * 1-5  cd /path/to/tapelab && .venv/bin/python -m tapelab.daily AAPL MSFT NVDA >> daily.log 2>&1

The Mac must be awake and Docker's Postgres running at that time. On a server, the same line works, or use a scheduler
such as EventBridge that starts the command in a container.

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
