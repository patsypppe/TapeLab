# TapeLab: Product & Plan

2026-10-23

## Vision

TapeLab is an AI trading research agent that reads a company's SEC filings and market data, explains its view on a stock with the evidence behind it, and is judged by a paper-trading portfolio rather than by claims.

It is built as a portfolio project for AI engineering and software engineering roles. Python runs the agents, retrieval and evaluation. A Java Spring Boot service is the backend API. Postgres stores everything, and a React dashboard shows the decisions and results.

What sets it apart is discipline: every decision is logged with its reasons before the outcome is known, every backtest is compared against buy-and-hold, and the README reports only numbers that were actually measured.

## Goals and success criteria

The project succeeds when one command turns a real stock into a real, logged decision, and the results are honest enough to defend in an interview.

**Goals**

- Build a working agent that combines filings analysis, price signals and a trader, end to end.
- Evaluate it properly: realistic backtests, standard benchmarks and a live paper portfolio.
- Show full-stack range: Python for AI, Java for the backend, Postgres, a React dashboard and AWS deployment.

**Non-goals**

- Trading real money. Nothing here is financial advice.
- High-frequency or low-latency trading, which would need C++ and different infrastructure.
- Beating the market as a claim. The honest outcome may be that the agent does not.

**Success criteria**

- A decision with reasons is produced and stored for at least 3 liquid tickers.
- Backtests include transaction costs, use only past data and are compared with buy-and-hold on dates after the model's training cutoff.
- The filings analyst is scored on the public FinanceBench sample, and the result is reported with the retrieval settings used.
- Paper trading runs daily for at least 3 months (a target, not a result).
- Gemini usage stays under the daily request quota.
- The README states only numbers that were measured.

## Product

You give TapeLab a stock, and it returns an insight (its view and the evidence) and a decision (buy, hold or sell, and how much). It then tracks that decision in a paper portfolio and reports how it did against buy-and-hold.

| Capability | What it does | Status |
| --- | --- | --- |
| Filings analysis | Retrieves relevant passages from 10-K and 10-Q filings and scores the outlook with Gemini | Retrieval built; live SEC fetch and pipeline wiring pending |
| Technical analysis | Scores the trend from a fast and slow moving-average crossover | Built |
| Trader | Blends analyst scores into a long or flat position | Built (basic) |
| Decision log | Stores every decision with reasons and evidence before the outcome is known | Planned |
| Backtesting | Next-day execution, transaction costs, buy-and-hold baseline | Built; tested on synthetic prices only |
| Debate and risk steps | Bull and bear analysts argue, a risk check can veto | Planned |
| Paper trading | Daily scheduled orders through a broker's paper account | Planned |
| Backend API | Java Spring Boot service for watchlist, decisions, portfolio and backtests | Early skeleton |
| Dashboard | React views of insights, decisions, portfolio and comparisons | Planned |

## Roadmap

The order below is deliberate: each step needs the one before it, and each has an exit test so progress is checkable.

1. **First real decision.** Load real prices and a real 10-K, score it with Gemini, store the decision in Postgres. Exit: one command prints and saves a decision with reasons for one ticker.
2. **Backend API.** Java endpoints for watchlist, decisions and portfolio, reading what Python writes. Exit: the demo's results are visible through the API.
3. **Backtests on real data.** Prices for 3 or more tickers, a test window after the model's training cutoff, costs and baselines. Exit: a reproducible report with buy-and-hold comparison.
4. **Richer agent.** News and sentiment analyst, bull and bear debate, risk check, moved onto LangGraph. Exit: ablations show whether each step helps, reported even if it does not.
5. **Retrieval evaluation.** FinanceBench sample and T2-RAGBench, comparing chunking and hybrid against dense search. Exit: a table of accuracy against configuration.
6. **Paper trading.** Daily scheduled run, orders through a broker's paper account, decisions logged before outcomes. Exit: a month of unbroken daily logs.
7. **Dashboard and deployment.** React app, Terraform on AWS, a short demo video. Exit: a public link and a README with measured results.

## Evaluation plan

A trading agent is only credible with evidence, so evaluation has three layers: question-answering benchmarks for the filings analyst, backtests for the strategy, and a forward paper-trading test that no look-ahead can contaminate.

| Benchmark | Tests | Use in TapeLab |
| --- | --- | --- |
| [FinanceBench](https://docs.patronus.ai/docs/research_and_differentiators/financebench) | Open-book questions on public company filings; 150 cases public | Headline accuracy for the filings analyst |
| [T2-RAGBench](https://arxiv.org/html/2506.12071v1) | Text-and-table questions built to judge retrieval | Retrieval ablations: chunking, hybrid against dense |
| FinQA, ConvFinQA, TAT-QA | Numerical reasoning over tables and text | Secondary checks |
| [StockBench](https://arxiv.org/html/2510.02209v1) | Daily buy, sell or hold over months, scored on return, drawdown and Sortino | Template for the trading evaluation |
| [InvestorBench](https://arxiv.org/html/2412.18174v1) | Financial decision tasks for LLM agents | Reference, with short historical windows |

**Backtesting rules**

- Decide at the close of day t, earn the return of day t+1.
- Charge transaction costs on every position change.
- Show the agent only data published on or before the decision date.
- Test on dates after the model's training cutoff, since a model can remember past price moves.
- Compare against buy-and-hold, and report every configuration tried, not only the best.
- Report return, Sharpe, Sortino, maximum drawdown and alpha.

**Paper trading**

- Alpaca is the likely broker; its current terms need checking at sign-up.
- A scheduler runs the agent once per trading day; each decision is logged before its outcome is known.
- Compare against buy-and-hold and an index fund over the same dates. If the agent only matches them, the honest conclusion is that it adds nothing.

## Risks, open questions and status

As of 2026-10-23 the code is a tested skeleton on [GitHub](https://github.com/patsypppe/tapelab) with 19 Python tests and 3 Java tests passing. It has produced no real results yet; the demo runs on synthetic prices and a made-up filing.

| Risk | Why it matters | Mitigation |
| --- | --- | --- |
| Model remembers past prices | Backtests on old dates look better than reality | Test only after the model's training cutoff; rely on paper trading |
| Overfitting from many trials | The best of many configurations is a lucky one | Log every trial; report the deflated Sharpe ratio |
| Gemini daily quota | Free-tier limits differ by source and may change | Cache scores per filing; request budget in code; check the AI Studio console |
| Noisy results | A few months of paper trading proves little | State uncertainty; use several tickers; never claim more than the data shows |
| Scope creep | Many components, one builder | Finish the first real decision before adding agents or a dashboard |

**Open questions**

- Which Gemini model and exact daily quota apply to the account?
- Which tickers go on the watchlist?
- Is Alpaca the broker, and does its paper account fit the plan?
- Hosting for the dashboard and API: AWS with Terraform, or something lighter?
