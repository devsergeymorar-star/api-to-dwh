from pydantic_settings import BaseSettings, SettingsConfigDict


class NbkSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NBK_")

    url: str = "https://nationalbank.kz/rss/get_rates.cfm"
    timeout: float = 30.0
