import logging
from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx
from dwh_common import RawRecord, request_json
from pydantic import BaseModel, ConfigDict

from connector_coingecko.settings import CoinGeckoSettings

log = logging.getLogger(__name__)


class MarketData(BaseModel):
    model_config = ConfigDict(extra="allow")

    current_price: dict[str, float]


class CoinHistory(BaseModel):
    """Only the shape we rely on downstream. Extra fields are kept in the raw payload as-is."""

    model_config = ConfigDict(extra="allow")

    id: str
    symbol: str
    # Absent for days before the coin was listed.
    market_data: MarketData | None = None


def build_client(settings: CoinGeckoSettings) -> httpx.Client:
    headers = {"accept": "application/json"}
    if key := settings.api_key.get_secret_value():
        headers["x-cg-demo-api-key"] = key
    return httpx.Client(base_url=settings.base_url, timeout=settings.timeout, headers=headers)


def extract(day: date, *, http: httpx.Client, settings: CoinGeckoSettings) -> Iterator[RawRecord]:
    """One record per coin: its market snapshot at 00:00 UTC of `day`."""
    for coin in settings.coins:
        data = request_json(
            http,
            f"/coins/{coin}/history",
            {"date": day.strftime("%d-%m-%Y"), "localization": "false"},
        )
        history = CoinHistory.model_validate(data)
        if history.market_data is None:
            log.warning("no market data for %s on %s, skipped", coin, day)
            continue
        payload: dict[str, Any] = data
        yield RawRecord(key=coin, payload=payload)
