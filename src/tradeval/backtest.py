from collections.abc import Callable


def backtest(closes: list[float], position_fn: Callable[[int], float], cost_bps: float = 5.0) -> list[float]:
    """Daily strategy returns. The position chosen at day t's close earns day t+1's return."""
    returns: list[float] = []
    prev = 0.0
    for t in range(len(closes) - 1):
        pos = position_fn(t)  # may only look at closes[: t + 1]
        daily = closes[t + 1] / closes[t] - 1
        cost = abs(pos - prev) * cost_bps / 10_000
        returns.append(pos * daily - cost)
        prev = pos
    return returns


def buy_and_hold(closes: list[float]) -> list[float]:
    """Daily returns of holding the asset the whole period."""
    return [closes[t + 1] / closes[t] - 1 for t in range(len(closes) - 1)]
