from fastapi import FastAPI
from pydantic import BaseModel

from .grounding import ungrounded_numbers

app = FastAPI(title="TapeLab")


class VerifyRequest(BaseModel):
    answer: str
    evidence: list[str]


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/verify")
def verify(req: VerifyRequest) -> dict:
    bad = sorted(ungrounded_numbers(req.answer, req.evidence))
    return {"grounded": not bad, "ungrounded_numbers": bad}
