import json
from datetime import date
from typing import Any
from uuid import uuid4

import pytest
from dwh_common import RawRecord, RawWriter


class FakeClient:
    def __init__(self) -> None:
        self.commands: list[str] = []
        self.inserts: list[dict[str, Any]] = []

    def command(self, cmd: str) -> None:
        self.commands.append(cmd)

    def insert(self, table: str, data: Any, column_names: Any, database: str | None) -> None:
        self.inserts.append(
            {"table": table, "data": data, "columns": column_names, "database": database}
        )


def test_ensure_table_creates_database_and_table() -> None:
    client = FakeClient()
    RawWriter(client, "raw", "openmeteo").ensure_table()
    assert client.commands[0] == "CREATE DATABASE IF NOT EXISTS raw"
    assert "CREATE TABLE IF NOT EXISTS raw.openmeteo" in client.commands[1]


def test_write_serializes_payload_and_metadata() -> None:
    client = FakeClient()
    batch = uuid4()
    written = RawWriter(client, "raw", "openmeteo").write(
        [RawRecord(key="almaty", payload={"t": 1.5, "city": "Алматы"})],
        date(2026, 10, 17),
        batch,
    )

    assert written == 1
    insert = client.inserts[0]
    assert (insert["table"], insert["database"]) == ("openmeteo", "raw")
    batch_id, _, source, partition_date, key, payload = insert["data"][0]
    assert (batch_id, source, partition_date, key) == (
        batch,
        "openmeteo",
        date(2026, 10, 17),
        "almaty",
    )
    assert json.loads(payload) == {"t": 1.5, "city": "Алматы"}


def test_write_skips_insert_when_nothing_extracted() -> None:
    client = FakeClient()
    assert RawWriter(client, "raw", "openmeteo").write([], date(2026, 10, 17), uuid4()) == 0
    assert client.inserts == []


@pytest.mark.parametrize("bad", ["Raw", "raw; DROP TABLE x", "1raw", ""])
def test_rejects_unsafe_identifiers(bad: str) -> None:
    with pytest.raises(ValueError):
        RawWriter(FakeClient(), "raw", bad)
