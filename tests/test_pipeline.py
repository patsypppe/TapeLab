from tapelab.agents.fundamentals import fundamentals_signal
from tapelab.agents.llm import RuleBasedLLM
from tapelab.agents.technical import technical_signal
from tapelab.agents.trader import decide
from tapelab.agents.types import Signal
from tapelab.demo import SAMPLE_FILING, synthetic_prices
from tradeval.backtest import backtest, buy_and_hold
from tradeval.metrics import sortino


def test_technical_bullish_on_uptrend_bearish_on_downtrend():
    up = [100 + i for i in range(40)]
    assert technical_signal(up).score > 0
    assert technical_signal(up[::-1]).score < 0
    assert technical_signal([1.0, 2.0]).score == 0.0


def test_fundamentals_reads_sample_filing():
    sig = fundamentals_signal(SAMPLE_FILING, RuleBasedLLM())
    assert sig.score > 0 and "positive" in sig.rationale


def test_trader_goes_long_only_when_blend_positive():
    assert decide([Signal("a", 0.5, ""), Signal("b", -0.2, "")]).position == 1.0
    assert decide([Signal("a", -0.5, ""), Signal("b", 0.2, "")]).position == 0.0


def test_backtest_uses_next_day_return_and_costs():
    closes = [100.0, 110.0, 99.0]
    r = backtest(closes, lambda t: 1.0, cost_bps=0)
    assert abs(r[0] - 0.10) < 1e-9 and abs(r[1] - (-0.10)) < 1e-9
    assert backtest(closes, lambda t: 0.0) == [0.0, 0.0]
    assert backtest(closes, lambda t: 1.0, cost_bps=100)[0] < r[0]


def test_backtest_cannot_see_the_future():
    closes = synthetic_prices(60)
    seen = []
    backtest(closes, lambda t: seen.append(t) or 0.0)
    assert seen == list(range(len(closes) - 1))  # decision at t gets only index t


def test_buy_and_hold_and_sortino():
    assert buy_and_hold([100, 110]) == [0.10000000000000009]
    assert sortino([0.01, 0.02, 0.01]) == 0.0
    assert sortino([0.02, -0.01, 0.03, -0.02]) != 0.0
