from collections.abc import Callable


def backtest_with_positions(
    closes: list[float], position_fn: Callable[[int], float], cost_bps: float = 5.0
) -> tuple[list[float], list[float]]:
    """Daily strategy returns and the position held each day. Day t's position earns day t+1."""
    returns: list[float] = []
    positions: list[float] = []
    prev = 0.0
    for t in range(len(closes) - 1):
        pos = position_fn(t)  # may only look at closes[: t + 1]
        daily = closes[t + 1] / closes[t] - 1
        cost = abs(pos - prev) * cost_bps / 10_000
        returns.append(pos * daily - cost)
        positions.append(pos)
        prev = pos
    return returns, positions


def backtest(closes: list[float], position_fn: Callable[[int], float], cost_bps: float = 5.0) -> list[float]:
    """Daily strategy returns. The position chosen at day t's close earns day t+1's return."""
    return backtest_with_positions(closes, position_fn, cost_bps)[0]


def buy_and_hold(closes: list[float]) -> list[float]:
    """Daily returns of holding the asset the whole period."""
    return [closes[t + 1] / closes[t] - 1 for t in range(len(closes) - 1)]
