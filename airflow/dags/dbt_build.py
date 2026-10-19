"""Rebuild staging and marts whenever any connector lands new raw data.

Scheduled on Assets, not on cron: there is no fixed time to guess, dbt runs right after a load.
"""

from __future__ import annotations

import functools
import operator

import pendulum
from airflow.sdk import DAG
from stand import DBT_IMAGE, connector_specs, container_task, raw_asset

with DAG(
    dag_id="dbt_build",
    description="dbt: raw -> staging -> marts in ClickHouse",
    # Any of the raw tables updated -> rebuild.
    schedule=functools.reduce(
        operator.or_, [raw_asset(spec["name"]) for spec in connector_specs()]
    ),
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    tags=["dbt"],
    default_args={"retries": 1, "retry_delay": pendulum.duration(minutes=2)},
) as dag:
    # Warns after 2 days without loads, fails after 4 (see dbt/models/staging/_sources.yml).
    freshness = container_task("source_freshness", DBT_IMAGE, command=["source", "freshness"])
    # One stale source must not block the marts built from the others.
    build = container_task("build", DBT_IMAGE, command=["build"], trigger_rule="all_done")
    freshness >> build
