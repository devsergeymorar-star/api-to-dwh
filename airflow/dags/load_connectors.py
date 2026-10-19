"""DAG factory: one DAG per connector from connectors.yaml.

Airflow knows only the image name and the date. The connector code, its dependencies
and its API logic live in the image; credentials come from Vault via Airflow Connections.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pendulum
import yaml
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import DAG, Param

CONFIG = Path(__file__).with_name("connectors.yaml")
DOCKER_URL = os.environ.get("CONNECTOR_DOCKER_URL", "unix://var/run/docker.sock")
NETWORK = os.environ.get("CONNECTOR_NETWORK", "bridge")
IMAGE_TEMPLATE = os.environ.get("CONNECTOR_IMAGE_TEMPLATE", "connector-{name}:dev")

# Resolved at run time from the `clickhouse_dwh` connection stored in Vault.
DWH_ENV = {
    "CH_HOST": "{{ conn.clickhouse_dwh.host }}",
    "CH_PORT": "{{ conn.clickhouse_dwh.port }}",
    "CH_USER": "{{ conn.clickhouse_dwh.login }}",
    "CH_PASSWORD": "{{ conn.clickhouse_dwh.password }}",
    "CH_DATABASE": "{{ conn.clickhouse_dwh.schema }}",
}

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
        DockerOperator(
            task_id="extract_load",
            image=image,
            command=["--date", LOAD_DATE],
            environment={**DWH_ENV, **spec.get("env", {})},
            docker_url=DOCKER_URL,
            network_mode=NETWORK,
            # Local `:dev` images are never in a registry; tagged registry images are pulled.
            force_pull=not image.endswith(":dev"),
            # The task runs on the Docker host, not inside the Airflow container: no shared tmp.
            mount_tmp_dir=False,
            auto_remove="success",
        )
    return dag


for _spec in yaml.safe_load(CONFIG.read_text())["connectors"]:
    globals()[f"load_{_spec['name']}"] = build_dag(_spec)
