import math
from itertools import product


def sharpe(returns: list[float], periods_per_year: int = 252, rf: float = 0.0) -> float:
    """Annualized return per unit of risk."""
    if len(returns) < 2:
        return 0.0
    ex = [r - rf / periods_per_year for r in returns]
    mean = sum(ex) / len(ex)
    var = sum((r - mean) ** 2 for r in ex) / (len(ex) - 1)
    return 0.0 if var == 0 else mean / math.sqrt(var) * math.sqrt(periods_per_year)


def max_drawdown(returns: list[float]) -> float:
    """Largest peak-to-trough loss of the compounded equity curve, as a positive fraction."""
    equity = peak = 1.0
    worst = 0.0
    for r in returns:
        equity *= 1 + r
        peak = max(peak, equity)
        worst = max(worst, (peak - equity) / peak)
    return worst


def cumulative_return(returns: list[float]) -> float:
    """Total compounded return over the period."""
    total = 1.0
    for r in returns:
        total *= 1 + r
    return total - 1


def alpha(strategy: list[float], benchmark: list[float]) -> float:
    """Cumulative excess return over the benchmark."""
    return cumulative_return(strategy) - cumulative_return(benchmark)


def ablation_grid(**axes: list) -> list[dict]:
    """Cartesian product of config axes, e.g. debate_rounds=[0,1,3], risk_team=[False,True]."""
    keys = list(axes)
    return [dict(zip(keys, vals)) for vals in product(*axes.values())]
