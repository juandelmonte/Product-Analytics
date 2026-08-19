# Architecture Decision Records

Key decisions and their rationale, recorded as lightweight ADRs.

---

## ADR-001 — Canonical identity key is the product `account_id`

- **Context**: three source systems use different identifiers (product
  `account_id`, CRM `company_id`, billing `customer_id`). We need one canonical
  key for joins.
- **Decision**: use the product `account_id` as canonical; CRM/billing map via
  an explicit `account_ref` linkage field.
- **Consequence**: no universal ID is invented; joins always go through
  `int_identity_mapping`; missing associations are surfaced as flags.

## ADR-002 — Three timestamps never conflated

- **Context**: business time, state-change time, and ingestion time answer
  different questions.
- **Decision**: preserve `event_at`, `effective_at`/`recorded_at`, and
  `source_updated_at`/`ingested_at` separately; metrics use `event_at`,
  state changes use `effective_at`, ingestion cursors use `source_updated_at`.
- **Consequence**: late events, future-effective changes, and duplicate
  detection are all expressible in SQL.

## ADR-003 — Ingestion disposition: append for events, merge for mutable records

- **Context**: events are immutable (except duplicates), CRM/billing are mutable.
- **Decision**: `append` for product events (dedup in dbt); `merge` (upsert by
  source primary key) for CRM and billing.
- **Consequence**: idempotent reruns; duplicate events preserved to bronze as a
  DQ scenario; mutable records always have a current row.

## ADR-004 — Deterministic, day-driven simulation

- **Context**: history must be reproducible; daily advance must be append-only.
- **Decision**: per-day RNG seeded from `f(SEED, day_index)`; a `sim_pending`
  queue delivers late/duplicate/future-effective records; `advance_day` is the
  single shared code path.
- **Consequence**: same seed → identical 24-month history; a day's output is
  independent of prior runs.

## ADR-005 — Medallion in ClickHouse with dbt owning staging/core/marts

- **Context**: ClickHouse has no `db.schema.table`; dlt writes raw, dbt
  transforms.
- **Decision**: `bronze` (dlt) → `staging` → `core` → `marts` (dbt). dbt
  `schema` maps to ClickHouse database; `source('bronze', …)` reads bronze.
- **Consequence**: clear ownership per layer; standardisation and dedup happen
  in staging; business logic in core; BI-ready tables in marts.

## ADR-006 — Airflow orchestrates by shelling out to services

- **Context**: business/ingestion/transformation logic must not live in Airflow.
- **Decision**: Airflow DAGs are BashOperators running
  `docker compose exec <service> <command>` against the running services.
- **Consequence**: separation of concerns preserved; DAGs stay thin; logic is
  testable in its owning service.

## ADR-007 — dbt-clickhouse version pin to dbt-core 1.10

- **Context**: `dbt-clickhouse` supports up to dbt-core 1.10.
- **Decision**: pin `dbt-core==1.10.23` + `dbt-clickhouse==1.10.2`,
  ClickHouse 25.3.
- **Consequence**: reproducible builds; the ClickHouse adapter constraint is
  respected.

## ADR-008 — Nine deliberate data-quality scenarios, each with a test

- **Context**: realistic source-quality problems must be demonstrated, not
  hidden.
- **Decision**: bake in late events, duplicates, mutable/late CRM,
  future-effective records, standardisation, missing associations, SCD, schema
  evolution — each with a dbt test.
- **Consequence**: `dbt test` proves the pipeline handles each problem; no
  silent cleaning.
