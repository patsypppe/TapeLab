from .types import Decision, Signal


def decide(signals: list[Signal], weights: dict[str, float] | None = None) -> Decision:
    """Combine analyst scores into a long-or-flat target position."""
    weights = weights or {}
    total = sum(weights.get(s.analyst, 1.0) for s in signals) or 1.0
    blended = sum(s.score * weights.get(s.analyst, 1.0) for s in signals) / total
    return Decision(position=1.0 if blended > 0 else 0.0, signals=tuple(signals))
