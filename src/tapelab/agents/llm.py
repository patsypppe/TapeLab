import re
from typing import ClassVar, Protocol


class LLM(Protocol):
    def score_fundamentals(self, evidence: list[str]) -> tuple[float, str]:
        """Return a bullish/bearish score in [-1, 1] and a short reason for the evidence."""
        ...


class RuleBasedLLM:
    """Offline stand-in: counts positive and negative words. Swap for a real model later."""

    POS: ClassVar[set[str]] = {"growth", "increased", "record", "improved", "strong", "profit"}
    NEG: ClassVar[set[str]] = {"decline", "decreased", "loss", "risk", "weak", "impairment", "lawsuit"}

    def score_fundamentals(self, evidence: list[str]) -> tuple[float, str]:
        words = re.findall(r"[a-z]+", " ".join(evidence).lower())
        pos = sum(w in self.POS for w in words)
        neg = sum(w in self.NEG for w in words)
        if pos + neg == 0:
            return 0.0, "no sentiment words"
        return (pos - neg) / (pos + neg), f"{pos} positive vs {neg} negative terms"
