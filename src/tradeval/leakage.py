"""Look-ahead checks: nothing dated after the decision date may reach the agents."""
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Doc:
    id: str
    published: date


def leaked(docs: list[Doc], decision_date: date) -> list[Doc]:
    """Docs an agent saw that were published after the decision date."""
    return [d for d in docs if d.published > decision_date]


def entry_date(decision: date, trading_days: list[date]) -> date | None:
    """First trading day strictly after the decision (no same-day-close execution)."""
    return next((d for d in sorted(trading_days) if d > decision), None)
