from datetime import date

from tradeval.leakage import Doc, entry_date, leaked
from tradeval.metrics import ablation_grid, alpha, max_drawdown, sharpe


def test_max_drawdown():
    assert abs(max_drawdown([0.1, -0.5, 0.2]) - 0.5) < 1e-9
    assert max_drawdown([0.01, 0.02]) == 0.0


def test_sharpe_zero_variance_and_sign():
    assert sharpe([0.01, 0.01, 0.01]) == 0.0
    assert sharpe([0.02, -0.01, 0.03, 0.0]) > 0


def test_alpha():
    assert abs(alpha([0.1], [0.04]) - 0.06) < 1e-9


def test_ablation_grid_size():
    g = ablation_grid(debate_rounds=[0, 1, 3], risk_team=[False, True])
    assert len(g) == 6 and {"debate_rounds": 3, "risk_team": True} in g


def test_leakage_detects_future_docs():
    d = date(2025, 3, 3)
    docs = [Doc("a", date(2025, 3, 1)), Doc("b", date(2025, 3, 4))]
    assert [x.id for x in leaked(docs, d)] == ["b"]


def test_entry_is_next_trading_day():
    days = [date(2025, 3, 3), date(2025, 3, 4), date(2025, 3, 5)]
    assert entry_date(date(2025, 3, 3), days) == date(2025, 3, 4)
    assert entry_date(date(2025, 3, 5), days) is None
