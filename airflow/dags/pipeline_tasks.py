"""Shared pipeline task builders for Airflow DAGs.

Each task shells out to `docker compose run --rm` against the compose project
via the mounted host docker socket. `run --rm` spawns a FRESH one-shot
container per task, which is required because the pipeline services (dlt, dbt)
have no long-running process - `docker compose exec` cannot target an exited
container.

This keeps ALL business/transformation logic in the services (api/dlt/dbt),
not in Airflow - Airflow only orchestrates the sequence.

The repo root is bind-mounted at /workspace inside the Airflow containers,
so the compose file is reachable at /workspace/docker-compose.yml. Note the
`-T` (no TTY) flag: these run non-interactively from the scheduler.
"""
from __future__ import annotations

from airflow.operators.bash import BashOperator

COMPOSE = "docker compose -f /workspace/docker-compose.yml --project-name saas-analytics"


def _bash(dag, task_id: str, command: str) -> BashOperator:
    return BashOperator(task_id=task_id, bash_command=command, dag=dag)


def sim_history_task(dag, days: int = 720) -> BashOperator:
    return _bash(
        dag,
        "generate_history",
        f"{COMPOSE} run --rm --no-deps api python -m app.sim history --days {days} ",
    )


def sim_day_task(dag) -> BashOperator:
    return _bash(
        dag,
        "advance_simulation_day",
        f"{COMPOSE} run --rm --no-deps api python -m app.sim day ",
    )


def dlt_ingest_task(dag, incremental: bool) -> BashOperator:
    flag = "--incremental" if incremental else ""
    return _bash(
        dag,
        "dlt_ingest",
        f"{COMPOSE} run --rm --no-deps dlt python -m pipelines.ingest {flag} ",
    )


def dbt_build_task(dag) -> BashOperator:
    # `dbt build` already runs models AND their data tests; this is the single
    # transform+verify step of the pipeline.
    return _bash(
        dag,
        "dbt_build",
        f"{COMPOSE} run --rm --no-deps dbt build ",
    )


def dbt_test_task(dag) -> BashOperator:
    # Standalone test run (no rebuild) - used where a build already happened
    # and the DAG only wants to re-assert data quality.
    return _bash(
        dag,
        "dbt_test",
        f"{COMPOSE} run --rm --no-deps dbt test ",
    )
