import json
from datetime import date

import httpx
import pytest

from tapelab import edgar
from tapelab.agents.gemini import GeminiLLM
from tapelab.prices import fetch_prices
from tapelab.retry import retry


@pytest.fixture
def waits(monkeypatch):
    """Records how long the code asked to wait, without actually waiting."""
    recorded: list[float] = []
    monkeypatch.setattr("tapelab.retry.time.sleep", recorded.append)
    return recorded


def status_error(code: int, headers: dict | None = None) -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://example.com")
    return httpx.HTTPStatusError("boom", request=request, response=httpx.Response(code, headers=headers, request=request))


def flaky(*failures):
    """A call that raises each failure in turn, then returns 'ok'."""
    pending = list(failures)
    calls = []

    def call():
        calls.append(1)
        if pending:
            raise pending.pop(0)
        return "ok"

    call.calls = calls
    return call


def test_retries_temporary_failures_with_growing_waits_then_succeeds(waits):
    call = flaky(status_error(503), httpx.ConnectError("down"))
    assert retry(call, attempts=3, base_delay=1.0) == "ok"
    assert len(call.calls) == 3 and waits == [1.0, 2.0]


def test_gives_up_after_the_allowed_attempts_and_raises_the_last_error(waits):
    call = flaky(*[status_error(500)] * 5)
    with pytest.raises(httpx.HTTPStatusError):
        retry(call, attempts=3)
    assert len(call.calls) == 3 and len(waits) == 2


def test_does_not_retry_a_real_error_such_as_not_found_or_a_bug(waits):
    for error in (status_error(404), status_error(400), ValueError("bad data")):
        call = flaky(error)
        with pytest.raises(type(error)):
            retry(call)
        assert len(call.calls) == 1
    assert waits == []


def test_honours_a_retry_after_header_but_caps_the_wait(waits):
    retry(flaky(status_error(429, {"Retry-After": "7"})), base_delay=1.0)
    retry(flaky(status_error(429, {"Retry-After": "9999"})), base_delay=1.0)
    assert waits == [7.0, 60.0]


def client_replying(*replies):
    """An HTTP client that answers with each reply in turn (an int status or a (status, json) pair)."""
    pending = list(replies)
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        reply = pending.pop(0) if len(pending) > 1 else pending[0]
        status, body = reply if isinstance(reply, tuple) else (reply, {})
        return httpx.Response(status, json=body)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    client.seen = seen
    return client


CHART = {"chart": {"error": None, "result": [{
    "meta": {"gmtoffset": 0}, "timestamp": [1735828200],
    "indicators": {"quote": [{"open": [1.0], "high": [1.0], "low": [1.0], "close": [1.0], "volume": [1]}],
                   "adjclose": [{"adjclose": [1.0]}]},
}]}}


def test_the_price_download_survives_a_busy_server(waits):
    client = client_replying(429, 503, (200, CHART))
    rows = fetch_prices("AAPL", date(2025, 1, 1), date(2025, 1, 10), client)
    assert len(rows) == 1 and len(client.seen) == 3


def test_the_price_download_does_not_hammer_a_missing_ticker(waits):
    client = client_replying(404)
    with pytest.raises(httpx.HTTPStatusError):
        fetch_prices("ZZZZ", date(2025, 1, 1), date(2025, 1, 10), client)
    assert len(client.seen) == 1


def test_the_sec_request_is_retried_too(waits, monkeypatch):
    monkeypatch.setattr(edgar, "PAUSE", 0)
    client = client_replying(502, (200, {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple"}}))
    assert edgar.lookup_cik(client, "aapl") == 320193 and len(client.seen) == 2


def test_the_gemini_call_is_retried_but_a_bad_key_is_not(waits):
    body = {"candidates": [{"content": {"parts": [{"text": json.dumps({"score": 0.5, "reason": "ok"})}]}}]}
    llm = GeminiLLM("key", "model", client=client_replying(429, (200, body)))
    assert llm.score_fundamentals(["x"]) == (0.5, "ok")

    bad = GeminiLLM("wrong", "model", client=client_replying(403))
    with pytest.raises(httpx.HTTPStatusError):
        bad.score_fundamentals(["x"])
    assert len(bad._http.seen) == 1
