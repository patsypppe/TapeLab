"""Replays trend rules over a price history and sets them against buy-and-hold."""
from dataclasses import dataclass
from itertools import pairwise

from .backtest import backtest_with_positions, buy_and_hold
from .metrics import cumulative_return, max_drawdown, sharpe, sortino
from .rules import TrendRule

MIN_DAYS_SCORED = 30  # fewer scored days than this says nothing


@dataclass(frozen=True)
class Result:
    name: str
    total_return: float
    sharpe: float
    sortino: float
    max_drawdown: float
    trades: int  # position changes while being scored
    invested: float  # share of scored days spent holding the stock


def summarize(name: str, returns: list[float], positions: list[float]) -> Result:
    """Turn a run's daily returns and positions into the numbers we compare."""
    trades = sum(1 for a, b in pairwise(positions) if a != b)
    invested = sum(1 for p in positions if p > 0) / len(positions)
    return Result(name, cumulative_return(returns), sharpe(returns), sortino(returns),
                  max_drawdown(returns), trades, invested)


def run_comparison(closes: list[float], rules: list[TrendRule], cost_bps: float = 5.0) -> list[Result]:
    """Buy-and-hold first, then each rule, all scored over the same days.

    Scoring starts once the slowest rule has enough history, so a slow rule is not
    compared with buy-and-hold over days it was still warming up.
    """
    start = max(rule.slow for rule in rules)
    if len(closes) - 1 - start < MIN_DAYS_SCORED:
        raise ValueError(f"Need at least {start + MIN_DAYS_SCORED + 1} closes, got {len(closes)}")
    held = buy_and_hold(closes)[start:]
    results = [summarize("buy and hold", held, [1.0] * len(held))]
    for rule in rules:
        returns, positions = backtest_with_positions(
            closes, lambda t, r=rule: r.position(closes[: t + 1]), cost_bps)
        results.append(summarize(rule.name, returns[start:], positions[start:]))
    return results
