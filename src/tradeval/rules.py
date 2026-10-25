"""Trading rules that can be replayed over history."""
from dataclasses import dataclass

from tapelab.agents.technical import technical_signal


@dataclass(frozen=True)
class TrendRule:
    """The live trend signal on its own: long while the fast average is above the slow one."""

    fast: int
    slow: int

    @property
    def name(self) -> str:
        return f"SMA {self.fast}/{self.slow}"

    def position(self, closes: list[float]) -> float:
        """Long (1.0) or flat (0.0), using only the closes it is given. Flat until `slow` closes exist."""
        return 1.0 if technical_signal(closes, self.fast, self.slow).score > 0 else 0.0
