from .types import Signal


def _sma(xs: list[float], n: int) -> float:
    return sum(xs[-n:]) / n


def technical_signal(closes: list[float], fast: int = 10, slow: int = 30) -> Signal:
    """Score the trend from a fast/slow moving-average crossover using only past closes."""
    if len(closes) < slow:
        return Signal("technical", 0.0, "not enough history")
    f, s = _sma(closes, fast), _sma(closes, slow)
    score = max(-1.0, min(1.0, (f - s) / s * 20))
    return Signal("technical", score, f"SMA{fast}={f:.2f} vs SMA{slow}={s:.2f}")
