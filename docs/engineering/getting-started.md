# Getting Started (developers)

How to run the full pipeline from scratch, advance it day by day, and find your
way around the code.

> This is a technical quick start. For the *why* and *what*, start at the
> [root README](../../README.md) and [`docs/README.md`](../README.md).

---

## Services

| Service      | Image / build        | Role                                                  |
|--------------|----------------------|-------------------------------------------------------|
| `postgres`   | `postgres:16`        | Operational source-of-truth (simulated SaaS database) |
| `api`        | `docker/api`         | FastAPI source-system-like APIs + simulation module   |
| `clickhouse` | `clickhouse-server`  | OLAP analytical warehouse (bronze/staging/core/marts) |
| `dbt`        | `docker/dbt`         | Transformation + testing (dbt-core + dbt-clickhouse)  |
| `dlt`        | `docker/dlt`         | Ingestion pipelines (historical + incremental)        |
| `airflow`    | `docker/airflow`     | Orchestration (profile `orchestration`)               |
| `evidence`   | `docker/evidence`    | Evidence business report over the marts (curated)     |

---

## Running the project (full pipeline)

The stack is **self-bootstrapping**: `docker compose up --build -d` builds the
images, starts the services, and the one-time `bootstrap` service runs the full
pipeline automatically (schema → 24 months of history → dlt ingest → dbt build
→ Evidence user). Airflow and Evidence start only after the bootstrap completes.

```powershell
# 1. Build + start everything (runs the full pipeline automatically)
docker compose up --build -d

# 2. Watch the one-time bootstrap (alembic-free: uses `sim reset` create_all)
docker compose logs -f bootstrap

# 3. Open the curated report
#    → http://localhost:3000   (Evidence)
```

On a **fresh clone / wiped volumes** the bootstrap runs the whole chain:

```
create ClickHouse DBs (bronze/staging/core/marts)
→ reset operational schema + generate 24 months of simulated history
→ dlt ingest into ClickHouse bronze
→ dbt build (staging → core → marts) + data tests
→ create the read-only Evidence user + grant
```

A completion marker on the `bootstrap-state` volume makes later `up`s a no-op.

> **One-command reset**: `. .\scripts\activate.ps1` then `reset-env` (or
> `make reset-environment`) = `down -v` + `build` + `up` + `docker compose
> wait bootstrap`.

> Docker Desktop must be running. If `docker compose` errors with a
> pipe/named-pipe message, start Docker Desktop first.
>
> **Windows dev note**: the `bootstrap` compose service and the Airflow DAGs
> orchestrate via the mounted docker socket with `docker compose run` - this
> resolves bind mounts correctly on Linux (the VPS deploy target), but on
> Docker Desktop (Windows) nested `run` cannot re-resolve `./api`-style mounts
> against the host path. On Windows, run the same chain from the host shell
> instead (`reset-env`), which is equivalent and fully validated.

### Daily advance + backfill

```powershell
docker compose run --rm api python -m app.sim day                 # advance 1 day
docker compose run --rm dlt python -m pipelines.ingest --incremental   # pull new/late data
docker compose run --rm dbt build                                   # update marts

# correct late data across prior dates
docker compose run --rm dbt build --full-refresh
```

### Airflow (orchestration)

Airflow starts automatically with `docker compose up` (its `airflow-init` runs
`db init`, then scheduler + webserver wait for the bootstrap to finish). To run
it explicitly, or after it was stopped:

```powershell
docker compose up -d airflow-scheduler airflow-webserver
# webserver UI: http://localhost:8081 (internal; not exposed on the VPS)
# `daily_pipeline` runs on a daily schedule: advance sim → ingest → build → test
```

If you want the one-time full initialisation as a DAG instead of the automatic
`bootstrap` service, trigger `historical_initialization` once from the UI.

### Evidence (curated report)

```powershell
docker compose up -d evidence
# report UI: http://localhost:3000
```

The Evidence report is the curated, version-controlled narrative over the
marts. The SQL behind every chart lives in `evidence/queries/` as plain
ClickHouse SQL.

---

## Warehouse layout

ClickHouse has no three-part `database.schema.table` hierarchy, so dbt maps its
`schema` directly onto a ClickHouse **database**. The medallion-like layout:

| Layer          | ClickHouse DB | Owner | What it is                                    |
|----------------|---------------|-------|-----------------------------------------------|
| bronze         | `bronze`      | dlt   | Raw, source-aligned data as ingested          |
| staging        | `staging`     | dbt   | Typed / standardised copies of bronze          |
| core           | `core`        | dbt   | Reusable intermediate business logic           |
| marts          | `marts`       | dbt   | Business-facing facts, dims, aggregates        |

All dbt tables use the `MergeTree` engine with an `ORDER BY tuple()` sort key
(see `dbt/dbt_project.yml`).

---

## Common commands

Run any of these from the repo root (PowerShell).

### Shortcuts (recommended)

Shortcuts are **project-scoped** - they live in `scripts/activate.ps1` and do
not touch your global PowerShell profile.

- **In VS Code:** new integrated terminals load them automatically (see
  `.vscode/settings.json`).
- **In any PowerShell window:** run `. .\scripts\activate.ps1` from the project root.

```powershell
dbt build            # full dbt pipeline: models + tests
dbt run              # models only
dbt test             # tests only
dbt debug            # verify dbt <-> ClickHouse connection
dbt docs generate    # (re)build the docs catalog into target/

dbt-docs             # regenerate docs, then serve in the FOREGROUND at
                     # http://localhost:8083 (Ctrl+C stops it).
                     # NOTE: dbt prints "localhost:8080" - that's the container
                     # port; on the host browse to 8083 (compose maps 8083->8080).

ch                   # interactive ClickHouse client on the analytics database
chq "select 1"       # one-shot SQL query

db-up                # start Postgres + ClickHouse in the background
psql                 # open psql on the operational database
api-up               # start the source API

sim history --days 720   # generate deterministic history
sim day                  # advance one day (append-only)
sim reset                # drop operational data

airflow-up           # start Airflow scheduler + webserver (runs with up by default)
reset-env            # full reset: down -v -> rebuild -> re-init the whole pipeline
```

> **Docs are served automatically by the stack.** On `docker compose up`, the
> `dbt` service runs `dbt docs serve` as a persistent server (after the
> bootstrap generates the catalog), so `http://localhost:8083` is available with
> no manual step. `dbt-docs` above is only needed when you want to regenerate
> AND serve docs in the foreground during development.
```

### Full commands (what the shortcuts expand to)

```powershell
docker compose build                                     # build/rebuild images
docker compose up -d postgres clickhouse api             # data infrastructure + source API
docker compose run --rm api alembic upgrade head         # apply operational schema
docker compose run --rm api python -m app.sim history --days 720   # generate history
docker compose run --rm dlt python -m pipelines.ingest   # historical ingest
docker compose run --rm dlt python -m pipelines.ingest --incremental  # incremental
docker compose run --rm dbt build                        # models + tests (109 checks)
docker compose exec clickhouse clickhouse-client --database analytics   # SQL client
```

---

## Project layout

```
.
├── docker-compose.yml        # the whole stack
├── Makefile                  # convenience commands
├── .env / .env.example       # stack settings (versions, credentials, seed)
├── scripts/
│   └── activate.ps1          # project-scoped PowerShell shortcuts
├── docs/                     # all documentation (see docs/README.md)
├── airflow/
│   └── dags/                 # Airflow DAGs (historical + daily)
├── evidence/                 # Evidence business report
│   ├── evidence.config.yaml  # project settings
│   ├── connection.yaml       # ClickHouse connector (env-injected creds)
│   ├── queries/              # reusable ClickHouse SQL
│   └── pages/                # report + exploration pages
├── docker/
│   ├── api/                  # FastAPI image
│   ├── dlt/                  # dlt ingestion image
│   ├── dbt/                  # dbt + dbt-clickhouse image
│   ├── airflow/              # Airflow image (docker CLI + compose)
│   └── evidence/             # Evidence serve image
├── api/                      # FastAPI app (source APIs + simulation module)
├── dlt/                      # dlt pipelines
└── dbt/                      # the dbt project
    ├── dbt_project.yml       # project + model configuration
    ├── profiles.yml          # ClickHouse connection profile
    ├── packages.yml          # dbt packages
    ├── macros/               # reusable Jinja + custom generic tests
    ├── models/
    │   ├── staging/          # stg_* tables
    │   ├── intermediate/     # int_* tables
    │   └── marts/            # fct_/dim_/agg_ tables
    └── tests/                # singular data-quality tests
```

---

## Notes & troubleshooting

- **Version pinning** lives in `.env`. `dbt-core` is pinned to the 1.10 line
  because `dbt-clickhouse` supports up to dbt-core 1.10.
- **ClickHouse version requirement** - the adapter requires ClickHouse 25.3+.
- **ClickHouse data** persists in the `clickhouse-data` Docker volume; reset
  with `docker compose down -v`.
- **Determinism** - the simulation uses the `SEED` variable from `.env`; the
  same seed reproduces the identical 24-month history.
