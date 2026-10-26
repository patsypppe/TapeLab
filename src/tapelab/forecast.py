"""A 10-trading-day price forecast: a likely range for each day, not a single guess."""
from dataclasses import dataclass
from itertools import pairwise
from math import exp, log, sqrt
from statistics import mean, stdev

HORIZON = 10  # trading days ahead
WINDOW = 60  # past daily returns used to estimate how much the stock moves
Z80 = 1.2816  # for a normal distribution, 80% of outcomes fall within this many standard deviations
MODELS = ("random_walk", "drift")


@dataclass(frozen=True)
class ForecastPoint:
    day_ahead: int
    median: float
    low: float  # 80% of outcomes are expected between low and high
    high: float


def forecast(closes: list[float], horizon: int = HORIZON, window: int = WINDOW,
             model: str = "random_walk") -> list[ForecastPoint]:
    """The range for each of the next `horizon` trading days, from the closes available now.

    random_walk: the middle stays at the last close, and the range widens with the square root
    of the days ahead. drift: the middle moves by the recent average daily return.
    Assumes steady volatility and normally distributed returns, so real crashes can fall outside.
    """
    if model not in MODELS:
        raise ValueError(f"Unknown model {model!r}; choose from {MODELS}")
    if len(closes) < window + 1:
        raise ValueError(f"Need at least {window + 1} closes, got {len(closes)}")
    returns = [log(b / a) for a, b in pairwise(closes[-(window + 1):])]
    sigma = stdev(returns)
    drift = mean(returns) if model == "drift" else 0.0
    start = log(closes[-1])
    points = []
    for day in range(1, horizon + 1):
        centre = start + drift * day
        spread = Z80 * sigma * sqrt(day)
        points.append(ForecastPoint(day, exp(centre), exp(centre - spread), exp(centre + spread)))
    return points
