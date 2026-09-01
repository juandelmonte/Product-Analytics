# Orchestration Design

Airflow owns **orchestration only**. No business logic, ingestion logic, or
transformation logic lives in Airflow — each step shells out to the service that
owns that concern.

## Separation of concerns

| Concern | Owner | Airflow's role |
|---------|-------|----------------|
| Business simulation | `api` (`app.sim`) | invoke `sim day` / `sim history` |
| Ingestion | `dlt` | invoke `pipelines.ingest` |
| Transformation + tests | `dbt` | invoke `dbt build` / `dbt test` |
| Ordering / retries / schedule | Airflow | the DAG |

## DAGs

```
historical_initialization (manual)
    generate_history (sim history --days 720)
        → dlt_ingest (full)
        → dbt_build
        → dbt_test

daily_pipeline (daily)
    advance_simulation_day (sim day)
        → dlt_ingest (--incremental)
        → dbt_build
        → dbt_test
```

## How tasks run

Each task is a `BashOperator` running:

```
docker compose -f /workspace/docker-compose.yml --project-name saas-analytics exec -T <service> <command>
```

- The repo root is bind-mounted at `/workspace` inside the Airflow containers.
- The host Docker socket is mounted so `docker compose exec` reaches the running
  services.
- `-T` disables TTY allocation (Airflow captures stdout cleanly).

## Idempotency & retries

- **Historical init** is idempotent: `sim reset` regenerates deterministically;
  dlt full load + `merge` dispositions upsert; dbt build is idempotent.
- **Daily** is idempotent: `sim day` is append-only; dlt incremental uses a
  persisted watermark; dbt build upserts.
- Each task has `retries` (set in the DAG default args) so transient failures
  (e.g. a flaky ClickHouse connection) are retried.

## Enable / run

```powershell
# one-time DB init
docker compose run --rm airflow-init

# start the scheduler + webserver (they run with `docker compose up` by default)
docker compose up -d airflow-scheduler airflow-webserver

# webserver UI: http://localhost:8081 (internal; not exposed on the VPS)
```

The daily DAG runs on a schedule; the historical DAG is triggered manually from
the UI or CLI.
