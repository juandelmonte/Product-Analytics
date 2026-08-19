"""Shared pipeline task builders for Airflow DAGs.

Each task shells out to `docker compose exec` against the running services.
This keeps ALL business/transformation logic in the services (api/dlt/dbt),
not in Airflow — Airflow only orchestrates the sequence.

The repo root is bind-mounted at /workspace inside the Airflow containers,
so the compose file is reachable at /workspace/docker-compose.yml.
"""
from __future__ import annotations

from airflow.operators.bash import BashOperator

COMPOSE = "docker compose -f /workspace/docker-compose.yml --project-name saas-analytics"


def sim_history_task(dag, days: int = 720) -> BashOperator:
    return BashOperator(
        task_id="generate_history",
        bash_command=f"{COMPOSE} exec -T api python -m app.sim history --days {days} ",
        dag=dag,
    )


def sim_day_task(dag) -> BashOperator:
    return BashOperator(
        task_id="advance_simulation_day",
        bash_command=f"{COMPOSE} exec -T api python -m app.sim day ",
        dag=dag,
    )


def dlt_ingest_task(dag, incremental: bool) -> BashOperator:
    flag = "--incremental" if incremental else ""
    return BashOperator(
        task_id="dlt_ingest",
        bash_command=f"{COMPOSE} exec -T dlt python -m pipelines.ingest {flag} ",
        dag=dag,
    )


def dbt_build_task(dag) -> BashOperator:
    return BashOperator(
        task_id="dbt_build",
        bash_command=f"{COMPOSE} exec -T dbt build ",
        dag=dag,
    )


def dbt_test_task(dag) -> BashOperator:
    return BashOperator(
        task_id="dbt_test",
        bash_command=f"{COMPOSE} exec -T dbt test ",
        dag=dag,
    )
