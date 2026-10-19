import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

log = logging.getLogger(__name__)

RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def _retry_after(response: httpx.Response) -> float:
    try:
        return float(response.headers.get("Retry-After", 0))
    except ValueError:  # HTTP-date form is rare for APIs; fall back to our own backoff
        return 0.0


def request(
    client: httpx.Client,
    url: str,
    params: Mapping[str, Any] | None = None,
    *,
    attempts: int = 4,
    backoff: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> httpx.Response:
    """GET with retries on network errors, 429 and 5xx (exponential backoff, honours Retry-After).

    Other 4xx are raised immediately: retrying a bad request only hides the bug.
    """
    for attempt in range(1, attempts + 1):
        retry_after = 0.0
        try:
            response = client.get(url, params=params)
            if response.status_code not in RETRYABLE_STATUSES:
                response.raise_for_status()
                return response
            retry_after = _retry_after(response)
            error: Exception = httpx.HTTPStatusError(
                f"retryable status {response.status_code}",
                request=response.request,
                response=response,
            )
        except httpx.TransportError as exc:
            error = exc

        if attempt == attempts:
            raise error
        delay = max(backoff * 2 ** (attempt - 1), retry_after)
        log.warning(
            "GET %s failed (%s), retry %d/%d in %.1fs", url, error, attempt, attempts, delay
        )
        sleep(delay)

    raise AssertionError("unreachable")


def request_json(
    client: httpx.Client,
    url: str,
    params: Mapping[str, Any] | None = None,
    **retry: Any,
) -> Any:
    """`request` + JSON decoding."""
    return request(client, url, params, **retry).json()
