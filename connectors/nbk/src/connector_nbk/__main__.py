import sys
from collections.abc import Sequence

import httpx
from dwh_common import run_connector

from connector_nbk import SOURCE
from connector_nbk.extract import extract
from connector_nbk.settings import NbkSettings


def main(argv: Sequence[str] | None = None) -> int:
    settings = NbkSettings()
    with httpx.Client(timeout=settings.timeout) as http:
        return run_connector(SOURCE, lambda day: extract(day, http=http, settings=settings), argv)


if __name__ == "__main__":
    sys.exit(main())
