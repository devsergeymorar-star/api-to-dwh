"""DAG factory: one DAG per connector from connectors.yaml.

Airflow knows only the image name and the date. The connector code, its dependencies
and its API logic live in the image; credentials come from Vault via Airflow Connections.
"""

from __future__ import annotations

from typing import Any

import pendulum
from airflow.sdk import DAG, Param
from stand import IMAGE_TEMPLATE, connector_specs, container_task, raw_asset

# Cron runs are stamped with the trigger time, so by default we load the previous day.
# A manual run can pass {"date": "YYYY-MM-DD"} to reload any day.
LOAD_DATE = "{{ params.date or macros.ds_add(ds, -1) }}"


def build_dag(spec: dict[str, Any]) -> DAG:
    name = spec["name"]
    image = IMAGE_TEMPLATE.format(name=name)

    with DAG(
        dag_id=f"load_{name}",
        description=f"{image} -> raw.{name}",
        schedule=spec.get("schedule", "0 3 * * *"),
        start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
        catchup=False,
        max_active_runs=1,
        tags=["connector", name],
        params={"date": Param(None, type=["null", "string"], format="date")},
        default_args={"retries": 2, "retry_delay": pendulum.duration(minutes=5)},
    ) as dag:
        container_task(
            "extract_load",
            image,
            command=["--date", LOAD_DATE],
            environment=spec.get("env", {}),
            # A successful load marks raw.<name> as updated and triggers dbt.
            outlets=[raw_asset(name)],
        )
    return dag


for _spec in connector_specs():
    globals()[f"load_{_spec['name']}"] = build_dag(_spec)
