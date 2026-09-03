"""Historical initialization DAG.

Generate 24 months of history → ingest → transform → validate.

This is the "initialize" workflow, run once per environment reset. It is
idempotent (sim reset + full ingest + full build) and can be rerun safely.
"""
from __future__ import annotations

from datetime import datetime

from airflow import DAG

from pipeline_tasks import dbt_build_task, dbt_test_task, dlt_ingest_task, sim_history_task

with DAG(
    dag_id="historical_initialization",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["analytics", "init"],
    doc_md=__doc__,
) as dag:
    generate_history = sim_history_task(dag, days=720)
    ingest = dlt_ingest_task(dag, incremental=False)
    build = dbt_build_task(dag)
    test = dbt_test_task(dag)

    generate_history >> ingest >> build >> test
