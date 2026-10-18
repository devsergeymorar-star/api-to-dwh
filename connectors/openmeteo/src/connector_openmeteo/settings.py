from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Location(BaseModel):
    name: str
    latitude: float
    longitude: float


DEFAULT_LOCATIONS = [
    Location(name="almaty", latitude=43.2389, longitude=76.8897),
    Location(name="astana", latitude=51.1694, longitude=71.4491),
    Location(name="shymkent", latitude=42.3417, longitude=69.5901),
]


class OpenMeteoSettings(BaseSettings):
    """OPENMETEO_LOCATIONS accepts JSON: [{"name": "...", "latitude": .., "longitude": ..}]."""

    model_config = SettingsConfigDict(env_prefix="OPENMETEO_")

    base_url: str = "https://api.open-meteo.com/v1/forecast"
    timeout: float = 30.0
    locations: list[Location] = DEFAULT_LOCATIONS
