from datetime import date
from typing import Any

import httpx
import pytest
import respx
from connector_coingecko.extract import build_client, extract
from connector_coingecko.settings import CoinGeckoSettings
from pydantic import SecretStr, ValidationError

BASE_URL = "https://api.coingecko.test/api/v3"


def history(coin: str, price: float | None) -> dict[str, Any]:
    body: dict[str, Any] = {"id": coin, "symbol": coin[:3], "name": coin.title()}
    if price is not None:
        body["market_data"] = {"current_price": {"usd": price, "kzt": price * 500}}
    return body


@respx.mock
def test_one_record_per_coin_and_skips_unlisted_days() -> None:
    respx.get(f"{BASE_URL}/coins/bitcoin/history").mock(
        return_value=httpx.Response(200, json=history("bitcoin", 81523.6))
    )
    route = respx.get(f"{BASE_URL}/coins/newcoin/history").mock(
        return_value=httpx.Response(200, json=history("newcoin", None))
    )
    settings = CoinGeckoSettings(base_url=BASE_URL, coins=["bitcoin", "newcoin"])

    with build_client(settings) as http:
        records = list(extract(date(2026, 10, 17), http=http, settings=settings))

    assert [r.key for r in records] == ["bitcoin"]
    assert records[0].payload["market_data"]["current_price"]["usd"] == 81523.6
    params = route.calls[0].request.url.params
    assert params["date"] == "17-10-2026"
    assert params["localization"] == "false"


@respx.mock
def test_api_key_goes_to_header_only_when_set() -> None:
    route = respx.get(f"{BASE_URL}/coins/bitcoin/history").mock(
        return_value=httpx.Response(200, json=history("bitcoin", 1.0))
    )
    for key, expected in [("", None), ("demo-123", "demo-123")]:
        settings = CoinGeckoSettings(base_url=BASE_URL, coins=["bitcoin"], api_key=SecretStr(key))
        with build_client(settings) as http:
            list(extract(date(2026, 10, 17), http=http, settings=settings))
        assert route.calls.last.request.headers.get("x-cg-demo-api-key") == expected


@respx.mock
def test_contract_change_fails_before_loading() -> None:
    respx.get(f"{BASE_URL}/coins/bitcoin/history").mock(
        return_value=httpx.Response(200, json={"error": "coin not found"})
    )
    settings = CoinGeckoSettings(base_url=BASE_URL, coins=["bitcoin"])
    with build_client(settings) as http, pytest.raises(ValidationError):
        list(extract(date(2026, 10, 17), http=http, settings=settings))
