import logging
import time
from collections.abc import Callable, Mapping
from typing import Any

import httpx

log = logging.getLogger(__name__)

RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


def request_json(
    client: httpx.Client,
    url: str,
    params: Mapping[str, Any] | None = None,
    *,
    attempts: int = 4,
    backoff: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    """GET a JSON document, retrying network errors, 429 and 5xx with exponential backoff.

    Other 4xx are raised immediately: retrying a bad request only hides the bug.
    """
    for attempt in range(1, attempts + 1):
        try:
            response = client.get(url, params=params)
            if response.status_code not in RETRYABLE_STATUSES:
                response.raise_for_status()
                return response.json()
            error: Exception = httpx.HTTPStatusError(
                f"retryable status {response.status_code}",
                request=response.request,
                response=response,
            )
        except httpx.TransportError as exc:
            error = exc

        if attempt == attempts:
            raise error
        delay = backoff * 2 ** (attempt - 1)
        log.warning(
            "GET %s failed (%s), retry %d/%d in %.1fs", url, error, attempt, attempts, delay
        )
        sleep(delay)

    raise AssertionError("unreachable")
