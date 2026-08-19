# Source Contracts

The exact contract of each source-like API the simulation exposes. These are the
spec the FastAPI service implements and the dlt pipelines consume. Contracts are
intentionally shaped like real source-system exports.

## Shared conventions

- **Base URL**: `http://api:8000/api/...`
- **Pagination**: `?limit=` (default 100, max 1000) and `?cursor=` (opaque,
  returned as `next_cursor` in the response body).
- **Incremental**: every collection supports `?updated_since=<ISO8601>` which
  returns rows whose `source_updated_at >= updated_since`, ordered by
  `source_updated_at` ascending, then by stable id.
- **Date range**: event collections support `?from=<ISO>&to=<ISO>` on event time.
- **Stable IDs**: every record has a source-specific string id that never
  changes across runs.
- **Deterministic ordering**: rows are ordered by `(source_updated_at, id)` so
  pagination is stable even when ties occur.
- **Timestamps**: every record carries `source_updated_at` (when the source
  record last changed) and events also carry `event_at` (when the business
  thing happened) and `ingested_at` (when our API served it — set by dlt on
  receipt).

## Response envelope

```json
{
  "data": [ ... ],
  "next_cursor": "opaque-or-null"
}
```

---

## 1. Product events — `GET /api/product-events`

Mixpanel-like event export.

| Field | Type | Notes |
|-------|------|-------|
| `event_id` | string | stable, unique (dedup key) |
| `event_name` | string | e.g. `user_signup`, `task_completed` |
| `distinct_id` | string | product user id |
| `account_id` | string | product account id (group key) |
| `event_at` | datetime | event time |
| `source_updated_at` | datetime | when the record was last written in the source |
| `properties` | JSON | free-form event properties |

- Query params: `from`, `to` (on `event_at`), `updated_since` (on
  `source_updated_at`), `limit`, `cursor`.
- Duplicates: the same `event_id` may appear more than once across pages/runs
  (client retries) — downstream dedup is required.

## 2. CRM contacts — `GET /api/crm/contacts`

HubSpot-like contact objects.

| Field | Type | Notes |
|-------|------|-------|
| `contact_id` | string | stable |
| `company_id` | string \| null | association; may be null then filled later |
| `email` | string | |
| `first_name` / `last_name` | string | |
| `lifecycle_stage` | string | subscriber/lead/mql/sql/customer/churned |
| `source_updated_at` | datetime | mutation cursor |

- Query params: `updated_since`, `limit`, `cursor`.
- Mutability: fields (and `company_id`) can change; each change bumps
  `source_updated_at`.

## 3. CRM companies — `GET /api/crm/companies`

| Field | Type | Notes |
|-------|------|-------|
| `company_id` | string | stable |
| `name` | string | |
| `industry` | string | mutable; values need standardisation |
| `company_size` | string | mutable (e.g. "1-10", "11-50") |
| `country` | string | mutable; `US`/`USA`/`United States` variants |
| `lead_source` | string | mutable |
| `lifecycle_stage` | string | mutable |
| `source_updated_at` | datetime | mutation cursor |

- Query params: `updated_since`, `limit`, `cursor`.

## 4. CRM deals — `GET /api/crm/deals`

| Field | Type | Notes |
|-------|------|-------|
| `deal_id` | string | stable |
| `company_id` | string | |
| `deal_stage` | string | e.g. `new`, `trial`, `closed_won`, `closed_lost` |
| `amount` | decimal | |
| `close_date` | date \| null | |
| `source_updated_at` | datetime | mutation cursor |

- Query params: `updated_since`, `limit`, `cursor`.

## 5. Billing customers — `GET /api/billing/customers`

Stripe-like customers.

| Field | Type | Notes |
|-------|------|-------|
| `customer_id` | string | stable |
| `email` | string | |
| `name` | string | |
| `source_updated_at` | datetime | mutation cursor |

- Query params: `updated_since`, `limit`, `cursor`.

## 6. Billing prices — `GET /api/billing/prices`

| Field | Type | Notes |
|-------|------|-------|
| `price_id` | string | stable |
| `product_id` | string | |
| `plan_code` | string | `free`/`trial`/`pro`/`enterprise` |
| `unit_amount` | decimal | per-seat price |
| `currency` | string | e.g. `usd` |
| `billing_frequency` | string | `monthly`/`annual` (needs standardisation) |
| `source_updated_at` | datetime | |

- Query params: `updated_since`, `limit`, `cursor`.

## 7. Billing subscriptions — `GET /api/billing/subscriptions`

| Field | Type | Notes |
|-------|------|-------|
| `subscription_id` | string | stable |
| `customer_id` | string | |
| `price_id` | string | |
| `status` | string | `trialing`/`active`/`past_due`/`canceled` |
| `seats` | int | quantity (subscription item) |
| `start_date` | datetime | |
| `ended_at` | datetime \| null | set on cancel |
| `recorded_at` | datetime | when the source recorded the change |
| `effective_at` | datetime | when the change takes effect (may be future) |
| `source_updated_at` | datetime | mutation cursor |

- Query params: `updated_since`, `limit`, `cursor`.
- Future-effective changes: `effective_at > recorded_at` must **not** be treated
  as current until `effective_at <= run date`.

## 8. Billing invoices — `GET /api/billing/invoices`

| Field | Type | Notes |
|-------|------|-------|
| `invoice_id` | string | stable |
| `customer_id` | string | |
| `subscription_id` | string | |
| `amount_due` | decimal | |
| `status` | string | `paid`/`open`/`void` |
| `created_at` | datetime | |
| `source_updated_at` | datetime | mutation cursor |

- Query params: `updated_since`, `limit`, `cursor`.

---

## Schema evolution (planned)

During the historical period, billing prices evolve from a single `plan` string
to a structured `plan_code`. Ingestion must handle both shapes:

- **Before the change**: rows have `plan` (e.g. `"Pro"`).
- **After the change**: rows have `plan` **and** `plan_code` (e.g. `"pro"`).

dlt is configured to preserve unknown columns; dbt staging coalesces
`plan_code = coalesce(plan_code, standardise(plan))`.
