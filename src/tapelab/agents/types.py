from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    analyst: str
    score: float  # -1 (bearish) .. +1 (bullish)
    rationale: str


@dataclass(frozen=True)
class Decision:
    position: float  # target exposure: 0 (flat) .. 1 (fully long)
    signals: tuple[Signal, ...]
