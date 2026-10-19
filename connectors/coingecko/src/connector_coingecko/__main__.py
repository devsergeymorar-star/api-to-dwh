import sys
from collections.abc import Sequence

from dwh_common import run_connector

from connector_coingecko import SOURCE
from connector_coingecko.extract import build_client, extract
from connector_coingecko.settings import CoinGeckoSettings


def main(argv: Sequence[str] | None = None) -> int:
    settings = CoinGeckoSettings()
    with build_client(settings) as http:
        return run_connector(SOURCE, lambda day: extract(day, http=http, settings=settings), argv)


if __name__ == "__main__":
    sys.exit(main())
