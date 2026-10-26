import random
from math import log

import pytest

from tapelab import forecast as forecast_module
from tapelab.forecast import forecast
from tradeval.forecast_eval import evaluate_forecasts, format_scores, walk_forward


def random_walk(n: int, vol: float = 0.015, drift: float = 0.0003, seed: int = 7) -> list[float]:
    rng = random.Random(seed)
    price, out = 100.0, []
    for _ in range(n):
        price *= 1 + rng.gauss(drift, vol)
        out.append(price)
    return out


def test_forecast_gives_ten_widening_ranges_centred_on_the_last_close():
    closes = random_walk(200)
    points = forecast(closes)
    assert [p.day_ahead for p in points] == list(range(1, 11))
    assert all(p.median == pytest.approx(closes[-1]) for p in points)
    assert all(p.low < p.median < p.high for p in points)
    width = [log(p.high / p.low) for p in points]
    assert width[3] / width[0] == pytest.approx(2.0)  # four days ahead is twice as wide: sqrt(4)


def test_a_calmer_stock_gets_a_narrower_range_than_a_wilder_one():
    calm = forecast(random_walk(200, vol=0.005))[-1]
    wild = forecast(random_walk(200, vol=0.03))[-1]
    assert (calm.high - calm.low) / calm.median < (wild.high - wild.low) / wild.median


def test_the_drift_model_moves_the_middle_with_the_recent_trend():
    rising = [100 * 1.004**i for i in range(100)]
    medians = [p.median for p in forecast(rising, model="drift")]
    assert medians == sorted(medians) and medians[0] > rising[-1]


def test_bad_input_is_rejected():
    with pytest.raises(ValueError):
        forecast(random_walk(30))  # needs window + 1 closes
    with pytest.raises(ValueError):
        forecast(random_walk(200), model="crystal_ball")
    with pytest.raises(ValueError):
        evaluate_forecasts(random_walk(40), "random_walk")


def test_ranges_are_well_calibrated_when_the_model_assumptions_hold():
    scores = evaluate_forecasts(random_walk(3000), "random_walk")
    for s in scores:
        assert 0.72 <= s.coverage <= 0.86, f"{s.horizon} days ahead: {s.coverage:.0%} inside the claimed 80% range"


def test_the_evaluation_reports_it_when_a_forecast_is_overconfident(monkeypatch):
    monkeypatch.setattr(forecast_module, "Z80", 0.2)  # ranges far too narrow for a claimed 80%
    scores = evaluate_forecasts(random_walk(3000), "random_walk")
    assert all(s.coverage < 0.4 for s in scores)


def test_drift_beats_the_random_walk_only_when_there_is_a_real_trend():
    trend = [100 * 1.003**i * (1 + random.Random(i).gauss(0, 0.002)) for i in range(800)]
    walk, drift = (evaluate_forecasts(trend, m)[-1] for m in ("random_walk", "drift"))
    assert drift.mean_error < walk.mean_error / 3


def test_no_forecast_depends_on_prices_that_come_later():
    base = random_walk(300)
    cut = 200
    garbage = random.Random(1)
    other = base[: cut + 1] + [garbage.uniform(1, 1000) for _ in range(len(base) - cut - 1)]
    for model in ("random_walk", "drift"):
        before = {o: p for o, p in walk_forward(base, model) if o <= cut}
        after = {o: p for o, p in walk_forward(other, model) if o <= cut}
        assert before == after and len(before) > 100


def test_scores_print_with_the_claimed_coverage_beside_the_measured_one():
    text = format_scores(evaluate_forecasts(random_walk(400), "random_walk"))
    assert "in range" in text and "(claimed)" in text and "80%" in text
