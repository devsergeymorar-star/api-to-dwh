from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class CoinGeckoSettings(BaseSettings):
    """COINGECKO_COINS accepts JSON: ["bitcoin", "ethereum"]. Ids are CoinGecko coin ids."""

    model_config = SettingsConfigDict(env_prefix="COINGECKO_")

    base_url: str = "https://api.coingecko.com/api/v3"
    timeout: float = 30.0
    # Optional demo key. Without it the public rate limit applies; 429s are retried.
    api_key: SecretStr = SecretStr("")
    coins: list[str] = ["bitcoin", "ethereum", "solana", "the-open-network"]
