from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ClickHouseSettings(BaseSettings):
    """Connection to the DWH. In Airflow these values come from a Connection, not from git."""

    model_config = SettingsConfigDict(env_prefix="CH_")

    host: str = "localhost"
    port: int = 8123
    user: str = "default"
    password: SecretStr = SecretStr("")
    database: str = "raw"
    secure: bool = False
