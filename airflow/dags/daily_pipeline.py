"""Daily pipeline DAG.

Advance the simulation one day → incremental dlt ingest → dbt build → tests.

Scheduled daily. Idempotent reruns are supported (incremental watermark +
merge dispositions + dbt build are all idempotent).
"""
from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG

from pipeline_tasks import dbt_build_task, dbt_test_task, dlt_ingest_task, sim_day_task

with DAG(
    dag_id="daily_pipeline",
    schedule=timedelta(days=1),
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["analytics", "daily"],
    doc_md=__doc__,
) as dag:
    advance = sim_day_task(dag)
    ingest = dlt_ingest_task(dag, incremental=True)
    build = dbt_build_task(dag)
    test = dbt_test_task(dag)

    advance >> ingest >> build >> test
