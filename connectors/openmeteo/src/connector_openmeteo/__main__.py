import sys
from collections.abc import Sequence

import httpx
from dwh_common import run_connector

from connector_openmeteo import SOURCE
from connector_openmeteo.extract import extract
from connector_openmeteo.settings import OpenMeteoSettings


def main(argv: Sequence[str] | None = None) -> int:
    settings = OpenMeteoSettings()
    with httpx.Client(timeout=settings.timeout) as http:
        return run_connector(SOURCE, lambda day: extract(day, http=http, settings=settings), argv)


if __name__ == "__main__":
    sys.exit(main())
