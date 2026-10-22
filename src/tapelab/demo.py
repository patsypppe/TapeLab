"""End-to-end demo on SYNTHETIC prices and a sample filing. Not evidence of real performance."""
import random

from tradeval.backtest import backtest, buy_and_hold
from tradeval.metrics import cumulative_return, max_drawdown, sharpe, sortino

from .agents.fundamentals import fundamentals_signal
from .agents.llm import RuleBasedLLM
from .agents.technical import technical_signal
from .agents.trader import decide

SAMPLE_FILING = """Revenue increased 12% year over year, with record operating profit.

| Year | Revenue |
| 2023 | 100 |
| 2024 | 112 |

Management cites strong demand, though supply risk and a lawsuit remain."""


def synthetic_prices(n: int = 500, seed: int = 7) -> list[float]:
    """Seeded random-walk prices, so runs are reproducible."""
    rng = random.Random(seed)
    price, out = 100.0, []
    for _ in range(n):
        price *= 1 + rng.gauss(0.0004, 0.012)
        out.append(price)
    return out


def main() -> None:
    closes = synthetic_prices()
    llm = RuleBasedLLM()
    fundamentals = fundamentals_signal(SAMPLE_FILING, llm)  # fixed filing: known before the window

    def position(t: int) -> float:
        signals = [technical_signal(closes[: t + 1]), fundamentals]
        return decide(signals).position

    agent, bh = backtest(closes, position), buy_and_hold(closes)
    print(f"{'':14}{'return':>9}{'sharpe':>9}{'sortino':>9}{'maxDD':>9}")
    for name, r in (("agent", agent), ("buy&hold", bh)):
        print(f"{name:14}{cumulative_return(r):>9.1%}{sharpe(r):>9.2f}{sortino(r):>9.2f}{max_drawdown(r):>9.1%}")
    print("fundamentals:", fundamentals.rationale)


if __name__ == "__main__":
    main()
