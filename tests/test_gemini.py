import json

import httpx
import pytest

from tapelab.agents.gemini import BudgetExceeded, GeminiLLM, RequestBudget


def _client(score, seen):
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        body = json.dumps({"score": score, "reason": "ok"})
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": body}]}}]})
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_parses_response_and_clamps_score():
    seen = []
    llm = GeminiLLM("k", "m", client=_client(5, seen))
    assert llm.score_fundamentals(["rev up"]) == (1.0, "ok")
    assert seen[0].headers["x-goog-api-key"] == "k" and "models/m:" in str(seen[0].url)


def test_budget_stops_requests():
    llm = GeminiLLM("k", "m", budget=RequestBudget(1), client=_client(0.2, []))
    llm.score_fundamentals(["x"])
    with pytest.raises(BudgetExceeded):
        llm.score_fundamentals(["x"])


def test_requires_key_and_model(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    with pytest.raises(RuntimeError):
        GeminiLLM()
    with pytest.raises(RuntimeError):
        GeminiLLM(api_key="k")
