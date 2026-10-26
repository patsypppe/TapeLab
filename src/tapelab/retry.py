"""Retries a call that failed for a temporary reason, waiting longer each time."""
import time
from collections.abc import Callable
from typing import TypeVar

import httpx

T = TypeVar("T")

RETRY_STATUSES = {429, 500, 502, 503, 504}  # too many requests, or the server had a hiccup
MAX_WAIT = 60.0  # never wait longer than this, even if a server asks


def is_temporary(error: Exception) -> bool:
    """True for failures worth trying again: timeouts, dropped connections, and busy-server statuses."""
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in RETRY_STATUSES
    return isinstance(error, httpx.TransportError)


def _wait_for(error: Exception, delay: float) -> float:
    """The planned delay, or longer if the server sent a Retry-After in seconds."""
    if isinstance(error, httpx.HTTPStatusError):
        asked = error.response.headers.get("Retry-After", "")
        if asked.isdigit():
            return min(max(delay, float(asked)), MAX_WAIT)
    return min(delay, MAX_WAIT)


def retry(call: Callable[[], T], attempts: int = 3, base_delay: float = 1.0) -> T:
    """Run `call`; on a temporary failure wait base_delay, then twice that, and so on, up to `attempts` tries."""
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as error:
            if attempt == attempts or not is_temporary(error):
                raise
            time.sleep(_wait_for(error, base_delay * 2 ** (attempt - 1)))
    raise AssertionError("unreachable")  # the loop always returns or raises
