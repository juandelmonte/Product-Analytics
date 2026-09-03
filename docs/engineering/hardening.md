# Hardening

Verification of the system under realistic operational stress: clean install,
repeated ingestion, daily refresh, late/duplicate/mutable/future-effective
data, schema evolution, backfill, and failure recovery.

## Commands

```powershell
# full reset + re-init (also exposed as `make reset-environment` / `reset-env`)
docker compose down -v
docker compose build
docker compose up -d postgres clickhouse api
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.sim reset
docker compose run --rm api python -m app.sim history --days 720
docker compose run --rm dlt python -m pipelines.ingest
docker compose run --rm dbt build

# backfill (correct late data): re-ingest incrementally + full-refresh dbt
docker compose run --rm dlt python -m pipelines.ingest --incremental
docker compose run --rm dbt build --full-refresh
```

## Verified scenarios

| Scenario | Result |
|----------|--------|
| Clean install (`down -v` → build → migrations → history → ingest → dbt) | ✅ 109/109 PASS on 720 days |
| Migrations from scratch (`alembic upgrade head` on empty DB) | ✅ all 3 migrations apply cleanly |
| Repeated ingestion (historical then incremental rerun) | ✅ no duplicate rows (636,232 = 636,232) |
| Daily refresh (`sim day` + incremental ingest) | ✅ only new rows appended |
| Late-arriving events | ✅ backfilled to correct `event_at` day |
| Duplicate events | ✅ deduped in staging; `fct_product_events` unique |
| Mutable CRM records | ✅ merge upsert; latest values current |
| Future-effective records | ✅ not in MRR before effective month |
| Schema evolution (`plan` → `plan_code`) | ✅ coalesced in staging |
| Backfill | ✅ incremental re-ingest + dbt `--full-refresh` |
| Failure recovery | ✅ idempotent reruns (watermarks + merge + build) |

## Bugs found & fixed during hardening

1. **`ended_at < start_date`** - expansion/churn could set a superseded row's
   `ended_at` to a date before its `start_date` when future-effective dates
   overlapped. Fixed by clamping `ended_at = max(day, start_date)` in
   `_churn`, `_expand`, and `_apply_billing_change`. Verified by
   `assert_subscription_dates_valid` on the full 720-day dataset.

## Reproducibility

The same `SEED` (42) reproduces the identical 720-day history. Determinism was
verified earlier (identical 30-day runs) and holds for the full run.
