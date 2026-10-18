from collections.abc import Iterable
from datetime import date
from uuid import UUID

from dwh_common import RawRecord, RawWriter, run_connector


class RecordingWriter(RawWriter):
    def __init__(self) -> None:
        self.ensured = False
        self.calls: list[tuple[list[RawRecord], date]] = []

    @property
    def table(self) -> str:
        return "raw.test"

    def ensure_table(self) -> None:
        self.ensured = True

    def write(self, records: Iterable[RawRecord], partition_date: date, batch_id: UUID) -> int:
        rows = list(records)
        self.calls.append((rows, partition_date))
        return len(rows)


def extract(day: date) -> list[RawRecord]:
    return [RawRecord(key="a", payload={"day": day.isoformat()})]


def test_loads_requested_date() -> None:
    writer = RecordingWriter()
    code = run_connector("test", extract, ["--date", "2026-10-01"], writer_factory=lambda _: writer)

    assert code == 0
    assert writer.ensured
    records, day = writer.calls[0]
    assert day == date(2026, 10, 1)
    assert records[0].payload == {"day": "2026-10-01"}


def test_dry_run_never_opens_dwh() -> None:
    def factory(_: str) -> RawWriter:
        raise AssertionError("dry run must not connect to ClickHouse")

    assert run_connector("test", extract, ["--date", "2026-10-01", "--dry-run"], factory) == 0
