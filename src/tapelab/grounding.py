"""Grounding check: every number in an answer must appear in the evidence it cites."""
import re

_NUM = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")


def _norm(n: str) -> str:
    return n.replace("$", "").replace(",", "").rstrip("%")


def numbers(text: str) -> set[str]:
    return {_norm(m) for m in _NUM.findall(text)}


def ungrounded_numbers(answer: str, evidence: list[str]) -> set[str]:
    """Numbers the answer asserts that no cited evidence contains."""
    seen = set().union(*(numbers(e) for e in evidence)) if evidence else set()
    return numbers(answer) - seen


def is_grounded(answer: str, evidence: list[str]) -> bool:
    return not ungrounded_numbers(answer, evidence)
