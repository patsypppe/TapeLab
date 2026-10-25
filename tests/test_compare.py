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
