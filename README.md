# api-to-dwh

Containerized API connectors that land raw data into a ClickHouse DWH, orchestrated by Airflow.

Each source is an independent connector with its own Docker image. Airflow only knows the image
name and the date to load. It does not install connector dependencies or run connector code in
its own process.

> Work in progress. Done: shared runtime + Open-Meteo connector.
> Next: docker-compose (Airflow + ClickHouse), CI/CD to GHCR, more connectors, dbt.

## Layout

```
libs/dwh-common/        shared runtime: HTTP retries, ClickHouse raw writer, CLI runner
connectors/openmeteo/   Open-Meteo daily weather -> raw.openmeteo
```

## Raw layer contract

Every connector writes to `raw.<source>` with the same schema:

| column | meaning |
|---|---|
| `_batch_id` | UUID of the run |
| `_loaded_at` | load timestamp, UTC |
| `_source` | connector name |
| `_partition_date` | logical date that was loaded |
| `_record_key` | business key of the object (e.g. city) |
| `payload` | the API object as JSON, untouched |

The raw layer is append-only. Re-runs and backfills add new batches. Deduplication
(latest `_loaded_at` per `_partition_date` + `_record_key`) happens in staging models.

## Local development

```bash
uv sync --all-packages
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run mypy libs/dwh-common/src connectors/openmeteo/src

# call the real API without touching ClickHouse
uv run connector-openmeteo --date 2026-10-17 --dry-run
```

## Docker

```bash
docker build -f connectors/openmeteo/Dockerfile -t connector-openmeteo .
docker run --rm -e CH_HOST=host.docker.internal connector-openmeteo --date 2026-10-17
```

ClickHouse connection is configured with `CH_HOST`, `CH_PORT`, `CH_USER`, `CH_PASSWORD`,
`CH_DATABASE` (default `raw`). Open-Meteo locations can be overridden with
`OPENMETEO_LOCATIONS='[{"name": "almaty", "latitude": 43.24, "longitude": 76.89}]'`.
