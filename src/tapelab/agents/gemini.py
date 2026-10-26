import json
import os

import httpx
from dotenv import load_dotenv

from ..retry import retry

load_dotenv()  # picks up a local .env if present; real env vars still win

URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

PROMPT = (
    "You are an equity analyst. Using ONLY the filing excerpts below, rate the company's "
    "outlook from -1 (very bearish) to 1 (very bullish). Reply as JSON: "
    '{{"score": <number>, "reason": "<one sentence>"}}\n\nExcerpts:\n{evidence}'
)


class BudgetExceeded(RuntimeError):
    pass


class RequestBudget:
    """Counts calls against a daily cap so batch runs stop before the quota does."""

    def __init__(self, limit: int):
        self.limit, self.used = limit, 0

    def spend(self) -> None:
        """Record one request, or raise if the daily cap is reached."""
        if self.used >= self.limit:
            raise BudgetExceeded(f"daily budget of {self.limit} requests reached")
        self.used += 1


class GeminiLLM:
    """Scores filing evidence with a Gemini model; key and model come from the environment."""

    def __init__(self, api_key: str | None = None, model: str | None = None,
                 budget: RequestBudget | None = None, client: httpx.Client | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = model or os.environ.get("GEMINI_MODEL")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not set")
        if not self.model:
            raise RuntimeError("GEMINI_MODEL is not set (pick the model with your quota)")
        self.budget = budget or RequestBudget(1400)  # headroom under a 1500/day cap
        self._http = client or httpx.Client(timeout=60)

    def score_fundamentals(self, evidence: list[str]) -> tuple[float, str]:
        """Ask Gemini for a bullish/bearish score and reason; clamps the score to [-1, 1]."""
        self.budget.spend()
        def request() -> httpx.Response:
            r = self._http.post(
                URL.format(model=self.model),
                headers={"x-goog-api-key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": PROMPT.format(evidence="\n---\n".join(evidence))}]}],
                    "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
                },
            )
            r.raise_for_status()
            return r

        r = retry(request, base_delay=2.0)
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        data = json.loads(text)
        return max(-1.0, min(1.0, float(data["score"]))), str(data["reason"])
