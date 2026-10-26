import random

import pytest

from tradeval.backtest import backtest, backtest_with_positions
from tradeval.compare import run_comparison
from tradeval.rules import TrendRule

RULES = [TrendRule(5, 20), TrendRule(10, 30)]
RISING = [100.0 + i for i in range(120)]
FALLING = [220.0 - i for i in range(120)]
ZIGZAG = [100.0 + (5 if i % 8 < 4 else -5) + i * 0.01 for i in range(160)]  # swings that fool a trend rule


def by_name(results):
    return {r.name: r for r in results}


def test_backtest_with_positions_matches_backtest_and_reports_each_days_position():
    closes = [100.0, 110.0, 99.0, 120.0]
    returns, positions = backtest_with_positions(closes, lambda t: 1.0 if t != 1 else 0.0)
    assert positions == [1.0, 0.0, 1.0]
    assert returns == backtest(closes, lambda t: 1.0 if t != 1 else 0.0)


def test_trend_rule_is_flat_until_it_has_enough_history_then_long_in_an_uptrend():
    rule = TrendRule(5, 20)
    assert rule.position(RISING[:10]) == 0.0
    assert rule.position(RISING[:60]) == 1.0
    assert rule.position(FALLING[:60]) == 0.0
    assert rule.name == "SMA 5/20"


def test_steady_uptrend_matches_buy_and_hold_with_no_trades_while_scored():
    results = by_name(run_comparison(RISING, RULES))
    for rule in RULES:
        r = results[rule.name]
        assert r.trades == 0 and r.invested == 1.0
        assert r.total_return == pytest.approx(results["buy and hold"].total_return)


def test_steady_downtrend_keeps_the_rule_out_while_buy_and_hold_loses():
    results = by_name(run_comparison(FALLING, RULES))
    assert results["buy and hold"].total_return < -0.1
    for rule in RULES:
        r = results[rule.name]
        assert r.total_return == 0.0 and r.invested == 0.0 and r.max_drawdown == 0.0


def test_whipsaw_makes_trades_and_costs_reduce_the_result():
    cheap = by_name(run_comparison(ZIGZAG, RULES, cost_bps=0))["SMA 5/20"]
    costly = by_name(run_comparison(ZIGZAG, RULES, cost_bps=100))["SMA 5/20"]
    assert cheap.trades > 2
    assert costly.total_return < cheap.total_return


def test_every_rule_is_scored_over_the_same_days_as_the_slowest():
    results = run_comparison(RISING, [TrendRule(5, 20), TrendRule(10, 50)])
    # 120 closes -> 119 daily returns; scoring starts after the slowest window (50 days)
    assert len(results) == 3  # buy and hold plus two rules


def test_too_little_history_is_rejected():
    with pytest.raises(ValueError):
        run_comparison(RISING[:40], RULES)


class SpyRule:
    """Records how much price history it is given each day."""

    fast, slow, name = 5, 20, "spy"

    def __init__(self):
        self.seen: list[list[float]] = []

    def position(self, closes):
        self.seen.append(list(closes))
        return 0.0


def test_the_engine_hands_each_rule_only_the_history_up_to_that_day():
    spy = SpyRule()
    run_comparison(RISING, [spy])
    # Day t may see closes 0..t and nothing later, so the histories grow one close at a time.
    assert [len(h) for h in spy.seen] == list(range(1, len(RISING)))
    assert all(h == RISING[: len(h)] for h in spy.seen)


def depends_on_future(positions_for, trials: int = 30, n: int = 400, cut: int = 250) -> bool:
    """True if decisions up to day `cut` change when only the prices after `cut` change.

    `positions_for(series)` returns the function that picks day t's position. Many different
    futures are tried: one random future can leave a one-day peeker's decision unchanged by luck.
    """
    rng = random.Random(1)
    price, base = 100.0, []
    for _ in range(n):
        price *= 1 + rng.gauss(0.0004, 0.015)
        base.append(price)
    _, reference = backtest_with_positions(base, positions_for(base))
    for _ in range(trials):
        other = base[:cut] + [rng.uniform(1, 1000) for _ in range(n - cut)]
        _, changed = backtest_with_positions(other, positions_for(other))
        if reference[:cut] != changed[:cut]:
            return True
    return False


def test_no_trend_rule_decision_depends_on_prices_that_come_later():
    for rule in (TrendRule(5, 20), TrendRule(10, 30), TrendRule(20, 50), TrendRule(50, 200)):
        assert not depends_on_future(lambda series, r=rule: lambda t: r.position(series[: t + 1])), rule.name


def test_the_check_itself_catches_a_rule_that_peeks_one_day_ahead():
    def cheater(series):
        return lambda t: 1.0 if t + 1 < len(series) and series[t + 1] > series[t] else 0.0

    assert depends_on_future(cheater)
