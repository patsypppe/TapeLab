"""Measures how good the forecast ranges were: python -m tradeval.forecast_eval AAPL MSFT NVDA."""
import argparse
from collections.abc import Iterator
from dataclasses import dataclass

from tapelab.db import connect
from tapelab.forecast import MODELS, WINDOW, ForecastPoint, forecast

from .report import load_history

HORIZONS = (1, 5, 10)
NOMINAL = 0.80  # the share of outcomes the range claims to contain


@dataclass(frozen=True)
class ForecastScore:
    model: str
    horizon: int
    coverage: float  # share of times the real price landed inside the range
    mean_error: float  # average distance of the middle from the real price, as a share of the price
    mean_width: float  # average width of the range, as a share of the price
    forecasts: int


def walk_forward(closes: list[float], model: str, window: int = WINDOW,
                 max_horizon: int = max(HORIZONS)) -> Iterator[tuple[int, list[ForecastPoint]]]:
    """Forecast from every origin day using only the closes up to that day."""
    for origin in range(window, len(closes) - max_horizon):
        yield origin, forecast(closes[: origin + 1], horizon=max_horizon, window=window, model=model)


def evaluate_forecasts(closes: list[float], model: str, horizons: tuple[int, ...] = HORIZONS,
                       window: int = WINDOW) -> list[ForecastScore]:
    """Score a model on every day it could have been used, against what really happened."""
    hits = {h: 0 for h in horizons}
    errors = {h: 0.0 for h in horizons}
    widths = {h: 0.0 for h in horizons}
    count = 0
    for origin, points in walk_forward(closes, model, window, max(horizons)):
        count += 1
        for h in horizons:
            actual, point = closes[origin + h], points[h - 1]
            hits[h] += point.low <= actual <= point.high
            errors[h] += abs(point.median - actual) / actual
            widths[h] += (point.high - point.low) / actual
    if count == 0:
        raise ValueError("Not enough history to score a forecast")
    return [ForecastScore(model, h, hits[h] / count, errors[h] / count, widths[h] / count, count)
            for h in horizons]


def format_scores(scores: list[ForecastScore]) -> str:
    """One row per model and horizon, with the nominal coverage shown for comparison."""
    lines = [f"{'model':<13}{'days':>5}{'in range':>10}{'(claimed)':>11}{'avg error':>11}{'avg width':>11}"]
    for s in scores:
        lines.append(f"{s.model:<13}{s.horizon:>5}{s.coverage:>10.0%}{NOMINAL:>11.0%}"
                     f"{s.mean_error:>11.1%}{s.mean_width:>11.1%}")
    return "\n".join(lines)


def main() -> None:
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="Score the 10-day forecast ranges on stored prices")
    parser.add_argument("tickers", nargs="+")
    args = parser.parse_args()
    with connect() as conn:
        for ticker in args.tickers:
            dates, closes = load_history(conn, ticker)
            try:
                scores = [s for model in MODELS for s in evaluate_forecasts(closes, model)]
            except ValueError as error:
                print(f"{ticker.upper()}: {error}\n")
                continue
            print(f"{ticker.upper()}: {dates[0]} to {dates[-1]}, {scores[0].forecasts} forecast days scored")
            print(format_scores(scores) + "\n")
    print("'in range' should be close to the claimed 80%. Forecasts on neighbouring days overlap, so the "
          "effective sample is smaller than the count shows. A range is not a prediction of direction.")


if __name__ == "__main__":
    main()
