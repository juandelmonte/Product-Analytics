# Ingestion Design

dlt ingests the source APIs into ClickHouse `bronze`. Ingestion is the boundary
between operational state (PostgreSQL) and analytical state (ClickHouse).

## Principles

1. **Incremental, not truncate-reload** - dlt cursors on `source_updated_at`
   (never `event_at`), so late-arriving and re-delivered records are not missed.
2. **Idempotent** - re-running a load does not duplicate data:
   - mutable collections (CRM, billing) use `merge` with a source primary key
     (upsert by key).
   - the event stream uses `append` + a persisted watermark; duplicates are
     *deliberately* preserved in bronze and deduped in dbt (DQ scenario).
3. **Preserve source metadata** - every row keeps `source_updated_at`,
   `event_at` / `effective_at` / `recorded_at`, and dlt adds `_dlt_*` load
   metadata. Analytics never mixes these timestamps.
4. **Schema evolution** - dlt's schema-evolution keeps unknown columns; the
   `plan` → `plan + plan_code` change is handled in dbt staging.

## Pipelines

| Pipeline | Endpoint(s) | Write disposition | Primary key (merge) |
|----------|-------------|-------------------|---------------------|
| `product_events` | `/api/product-events` | append | - (dedup in dbt) |
| `crm` | contacts, companies, deals | merge | contact_id / company_id / deal_id |
| `billing` | customers, prices, subscriptions, invoices | merge | customer_id / price_id / subscription_id / invoice_id |

## Watermarks

- **Product events**: `source_updated_at`, seeded at epoch for the historical
  load; the watermark advances with each run.
- **CRM/billing**: `source_updated_at`, seeded at epoch; `merge` ensures
  changed records are re-read and upserted.

## Late-arriving events

A late event has `event_at` (past) but `source_updated_at` (now, when it became
available). Because the cursor is on `source_updated_at`, the late event is
picked up on the next run and lands in bronze with its true `event_at`. dbt
attributes it to the correct analytical day.

## Duplicate events

A client retry re-delivers the same `event_id`. Bronze keeps both rows (append);
`stg_product_events` dedups on `event_id`, keeping the first by
`source_updated_at`.

## Commands

```
docker compose run --rm dlt python -m pipelines.ingest                # historical
docker compose run --rm dlt python -m pipelines.ingest --incremental   # incremental
docker compose run --rm dlt python -m pipelines.ingest --since <ISO>   # from a watermark
```

## Validated behaviour

- Historical load populates all 8 bronze tables.
- Incremental re-run after history: no duplicate rows (idempotent).
- After `sim day`: incremental picks up only the new day's rows; Postgres and
  ClickHouse counts match exactly (10853 = 10853).
