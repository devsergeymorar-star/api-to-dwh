from collections.abc import Iterator
from datetime import date
from typing import Any

import httpx
from dwh_common import RawRecord, request_json
from pydantic import BaseModel, ConfigDict

from connector_openmeteo.settings import OpenMeteoSettings

DAILY_VARS = (
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "wind_speed_10m_max",
)
HOURLY_VARS = (
    "temperature_2m",
    "relative_humidity_2m",
    "precipitation",
    "wind_speed_10m",
)


class ForecastResponse(BaseModel):
    """Only the shape we rely on downstream. Extra fields are kept in the raw payload as-is."""

    model_config = ConfigDict(extra="allow")

    latitude: float
    longitude: float
    timezone: str
    daily: dict[str, list[Any]]
    hourly: dict[str, list[Any]]


def extract(day: date, *, http: httpx.Client, settings: OpenMeteoSettings) -> Iterator[RawRecord]:
    """One record per location: the full API response for that day."""
    for location in settings.locations:
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "start_date": day.isoformat(),
            "end_date": day.isoformat(),
            "daily": ",".join(DAILY_VARS),
            "hourly": ",".join(HOURLY_VARS),
            "timezone": "UTC",
        }
        data = request_json(http, settings.base_url, params)
        # Fail loudly if the API changed its contract, before anything lands in the DWH.
        ForecastResponse.model_validate(data)
        yield RawRecord(key=location.name, payload={"location": location.name, **data})
