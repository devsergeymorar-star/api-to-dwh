from datetime import date
from typing import Any

import httpx
import pytest
import respx
from connector_openmeteo.extract import extract
from connector_openmeteo.settings import Location, OpenMeteoSettings
from pydantic import ValidationError

BASE_URL = "https://api.open-meteo.test/v1/forecast"


def settings(*locations: Location) -> OpenMeteoSettings:
    return OpenMeteoSettings(base_url=BASE_URL, locations=list(locations))


def forecast(lat: float, lon: float) -> dict[str, Any]:
    return {
        "latitude": lat,
        "longitude": lon,
        "timezone": "UTC",
        "daily": {"time": ["2026-10-17"], "temperature_2m_max": [14.2]},
        "hourly": {"time": ["2026-10-17T00:00"], "temperature_2m": [6.1]},
    }


@respx.mock
def test_one_record_per_location_with_full_payload() -> None:
    route = respx.get(BASE_URL).mock(
        side_effect=[
            httpx.Response(200, json=forecast(43.25, 76.875)),
            httpx.Response(200, json=forecast(51.125, 71.5)),
        ]
    )
    cfg = settings(
        Location(name="almaty", latitude=43.2389, longitude=76.8897),
        Location(name="astana", latitude=51.1694, longitude=71.4491),
    )
    with httpx.Client() as http:
        records = list(extract(date(2026, 10, 17), http=http, settings=cfg))

    assert [r.key for r in records] == ["almaty", "astana"]
    assert records[0].payload["location"] == "almaty"
    assert records[0].payload["daily"]["temperature_2m_max"] == [14.2]

    params = route.calls[0].request.url.params
    assert params["start_date"] == params["end_date"] == "2026-10-17"
    assert params["latitude"] == "43.2389"
    assert "temperature_2m_max" in params["daily"]


@respx.mock
def test_contract_change_fails_before_loading() -> None:
    respx.get(BASE_URL).mock(return_value=httpx.Response(200, json={"error": False}))
    cfg = settings(Location(name="almaty", latitude=43.2, longitude=76.9))
    with httpx.Client() as http, pytest.raises(ValidationError):
        list(extract(date(2026, 10, 17), http=http, settings=cfg))
