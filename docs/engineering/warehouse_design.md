# Warehouse Design

The analytical warehouse is ClickHouse, structured as a medallion-like flow with
a clear owner and responsibility per layer. dbt reads bronze via `source()` and
builds staging → core → marts.

## Layers

| Layer | ClickHouse DB | Owner | Responsibility |
|-------|---------------|-------|----------------|
| bronze | `bronze` | dlt | Raw, source-aligned data as ingested. Nothing is cleaned here. |
| staging | `staging` | dbt | Type casting, basic standardisation, dedup (events), SCD-current selection. |
| core | `core` | dbt | Reusable business logic: identity mapping, activation, subscription history. |
| marts | `marts` | dbt | Business-facing **star schema**: conformed `dim_*` dimensions + `fct_*` facts. |

## Marts: star schema

The consumption layer is a **star schema** (Kimball-style), not a set of wide,
self-contained facts:

- **Dimensions** (`dim_*`) hold descriptive attributes and are conformed — one
  definition, reused by every fact that references them. Current dims:
  `dim_accounts` (account + CRM attributes + current plan), `dim_plans`
  (billing catalog), `dim_features` (feature labels), `dim_dates` (calendar).
- **Facts** (`fct_*`) hold measures and **foreign keys** to dimensions. They do
  not re-embed dimension attributes.
- Queries join dimensions at query time by natural key (`account_id`,
  `plan_code`, `feature_code`, `day_date`).

Why this, on ClickHouse? Columnar stores make small dimension joins cheap, so a
normalised star is fine; what we avoid is the *other* extreme — copying every
dimension column into every fact, which duplicates data and drifts definitions.
Dimensions are defined once, conformed, and joined. If a specific query ever
needs a hot-path denormalisation, that's a measured physical-layer optimisation,
not the default shape.

Only entities that add descriptive attributes to multiple facts are materialised
as dimensions. `User`, `Workspace`, `Project`, and `Subscription` are referenced
by key on their facts rather than given a physical `dim_*` table, because their
descriptive attributes (if any) already live on the fact rows.

## ClickHouse specifics

- No `database.schema.table` hierarchy: dbt maps `schema` → ClickHouse
  **database**. The `generate_schema_name` macro keeps names flat.
- Tables use `MergeTree` with `ORDER BY tuple()` (configured in
  `dbt_project.yml`).
- dlt writes tables plainly into the `bronze` database (dataset name left None).

## Time semantics

Three timestamps are preserved end-to-end and never conflated:

- `event_at` — when the business thing happened (metric attribution).
- `effective_at` / `recorded_at` — when a state change is true vs when it was
  recorded (future-effective logic).
- `source_updated_at` / `_dlt_ingested_at` — when the row was written / loaded
  (ingestion diagnostics and watermarks).

## Source() contract with dbt-clickhouse

The dbt adapter maps `source(name, table)` to ClickHouse `name.table`. dbt will
therefore define a source named `bronze` whose tables match the dlt table names
(e.g. `bronze.product_events`).

## Grain rule

Every model declares its grain in a header comment and enforces it with a
`unique` test on the grain key. Layers are not created without a reason.
