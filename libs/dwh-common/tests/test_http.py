import httpx
import pytest
import respx
from dwh_common import request, request_json

URL = "https://api.example.com/data"


def no_sleep(_: float) -> None:
    pass


@respx.mock
def test_retries_5xx_then_succeeds() -> None:
    route = respx.get(URL).mock(
        side_effect=[httpx.Response(503), httpx.Response(200, json={"ok": True})]
    )
    with httpx.Client() as client:
        assert request_json(client, URL, sleep=no_sleep) == {"ok": True}
    assert route.call_count == 2


@respx.mock
def test_gives_up_after_attempts() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(429))
    with httpx.Client() as client, pytest.raises(httpx.HTTPStatusError):
        request_json(client, URL, attempts=3, sleep=no_sleep)
    assert route.call_count == 3


@respx.mock
def test_does_not_retry_client_errors() -> None:
    route = respx.get(URL).mock(return_value=httpx.Response(400))
    with httpx.Client() as client, pytest.raises(httpx.HTTPStatusError):
        request_json(client, URL, sleep=no_sleep)
    assert route.call_count == 1


@respx.mock
def test_retries_network_errors_with_backoff() -> None:
    respx.get(URL).mock(side_effect=[httpx.ConnectError("boom"), httpx.Response(200, json=[1])])
    delays: list[float] = []
    with httpx.Client() as client:
        assert request_json(client, URL, backoff=2.0, sleep=delays.append) == [1]
    assert delays == [2.0]


@respx.mock
def test_honours_retry_after_on_rate_limit() -> None:
    respx.get(URL).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "30"}),
            httpx.Response(200, text="<ok/>"),
        ]
    )
    delays: list[float] = []
    with httpx.Client() as client:
        assert request(client, URL, sleep=delays.append).text == "<ok/>"
    assert delays == [30.0]
