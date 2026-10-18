import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any, Protocol
from uuid import UUID

_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_]*$")

# Raw layer is append-only: every run adds a new batch, nothing is updated in place.
# Deduplication (latest _loaded_at per _partition_date + _record_key) happens downstream
# in staging models, so a re-run or backfill never loses history.
RAW_TABLE_DDL = """
CREATE TABLE IF NOT EXISTS {database}.{table}
(
    _batch_id       UUID,
    _loaded_at      DateTime64(3, 'UTC'),
    _source         LowCardinality(String),
    _partition_date Date,
    _record_key     String,
    payload         String
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(_partition_date)
ORDER BY (_partition_date, _record_key, _loaded_at)
"""

COLUMNS = ["_batch_id", "_loaded_at", "_source", "_partition_date", "_record_key", "payload"]


class ClickHouseClient(Protocol):
    def command(self, cmd: str) -> Any: ...

    def insert(self, table: str, data: Any, column_names: Any, database: str | None) -> Any: ...


@dataclass(frozen=True)
class RawRecord:
    """One API object as it came from the source, plus a business key for later dedup."""

    key: str
    payload: Mapping[str, Any]


def _identifier(value: str) -> str:
    if not _IDENTIFIER.match(value):
        raise ValueError(f"invalid ClickHouse identifier: {value!r}")
    return value


class RawWriter:
    def __init__(self, client: ClickHouseClient, database: str, source: str) -> None:
        self._client = client
        self._database = _identifier(database)
        self._source = _identifier(source)

    @property
    def table(self) -> str:
        return f"{self._database}.{self._source}"

    def ensure_table(self) -> None:
        self._client.command(f"CREATE DATABASE IF NOT EXISTS {self._database}")
        self._client.command(RAW_TABLE_DDL.format(database=self._database, table=self._source))

    def write(self, records: Iterable[RawRecord], partition_date: date, batch_id: UUID) -> int:
        loaded_at = datetime.now(UTC)
        rows = [
            [
                batch_id,
                loaded_at,
                self._source,
                partition_date,
                record.key,
                json.dumps(record.payload, ensure_ascii=False, separators=(",", ":")),
            ]
            for record in records
        ]
        if rows:
            self._client.insert(self._source, rows, column_names=COLUMNS, database=self._database)
        return len(rows)
