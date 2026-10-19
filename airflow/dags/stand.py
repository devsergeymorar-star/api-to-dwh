"""Settings shared by the connector DAGs and the dbt DAG (not a DAG file itself)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from airflow.providers.docker.operators.docker import DockerOperator
from airflow.sdk import Asset

CONNECTORS_CONFIG = Path(__file__).with_name("connectors.yaml")
DOCKER_URL = os.environ.get("CONNECTOR_DOCKER_URL", "unix://var/run/docker.sock")
NETWORK = os.environ.get("CONNECTOR_NETWORK", "bridge")
IMAGE_TEMPLATE = os.environ.get("CONNECTOR_IMAGE_TEMPLATE", "connector-{name}:dev")
DBT_IMAGE = os.environ.get("DBT_IMAGE", "dbt-runner:dev")

# Resolved at run time from the `clickhouse_dwh` connection stored in Vault.
DWH_ENV = {
    "CH_HOST": "{{ conn.clickhouse_dwh.host }}",
    "CH_PORT": "{{ conn.clickhouse_dwh.port }}",
    "CH_USER": "{{ conn.clickhouse_dwh.login }}",
    "CH_PASSWORD": "{{ conn.clickhouse_dwh.password }}",
    "CH_DATABASE": "{{ conn.clickhouse_dwh.schema }}",
}


def connector_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = yaml.safe_load(CONNECTORS_CONFIG.read_text())["connectors"]
    return specs


def raw_asset(source: str) -> Asset:
    """The raw table a connector lands into; downstream DAGs are scheduled on it."""
    return Asset(f"raw_{source}")


def container_task(task_id: str, image: str, **kwargs: Any) -> DockerOperator:
    """Run `image` on the Docker host, in the DWH network, with DWH credentials."""
    env = {**DWH_ENV, **kwargs.pop("environment", {})}
    return DockerOperator(
        task_id=task_id,
        image=image,
        environment=env,
        docker_url=DOCKER_URL,
        network_mode=NETWORK,
        # Local `:dev` images are never in a registry; tagged registry images are pulled.
        force_pull=not image.endswith(":dev"),
        # The task runs on the Docker host, not inside the Airflow container: no shared tmp.
        mount_tmp_dir=False,
        auto_remove="success",
        **kwargs,
    )
