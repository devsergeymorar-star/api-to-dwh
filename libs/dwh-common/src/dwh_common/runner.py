import argparse
import logging
import sys
from collections.abc import Callable, Iterable, Sequence
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

from dwh_common.raw_writer import RawRecord, RawWriter
from dwh_common.settings import ClickHouseSettings

log = logging.getLogger("connector")

Extract = Callable[[date], Iterable[RawRecord]]
WriterFactory = Callable[[str], RawWriter]


def _clickhouse_writer(source: str) -> RawWriter:
    import clickhouse_connect

    settings = ClickHouseSettings()
    client = clickhouse_connect.get_client(
        host=settings.host,
        port=settings.port,
        username=settings.user,
        password=settings.password.get_secret_value(),
        secure=settings.secure,
    )
    return RawWriter(client, settings.database, source)


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract one day from the API into the raw layer")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=datetime.now(UTC).date() - timedelta(days=1),
        help="logical date to load, YYYY-MM-DD (default: yesterday, UTC)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="call the API and print a sample record, do not touch ClickHouse",
    )
    return parser.parse_args(argv)


def run_connector(
    source: str,
    extract: Extract,
    argv: Sequence[str] | None = None,
    writer_factory: WriterFactory = _clickhouse_writer,
) -> int:
    """Common entrypoint of every connector image: parse CLI, extract, land raw rows."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
    )
    args = _parse_args(argv)
    batch_id = uuid4()
    log.info("source=%s date=%s batch=%s dry_run=%s", source, args.date, batch_id, args.dry_run)

    records = list(extract(args.date))
    log.info("extracted %d records", len(records))

    if args.dry_run:
        if records:
            print(records[0])
        return 0

    writer = writer_factory(source)
    writer.ensure_table()
    written = writer.write(records, args.date, batch_id)
    log.info("wrote %d rows to %s", written, writer.table)
    return 0
