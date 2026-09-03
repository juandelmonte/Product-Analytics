# Data Quality Validation - Results

Each of the nine intentional data-quality scenarios was run through the full
chain (source → ingestion → transformation → detection → correction →
analytical output) and has a passing dbt test. This file records the verified
result per scenario.

## Summary

| # | Scenario | Detection | Treatment | Test | Status |
|---|----------|-----------|-----------|------|--------|
| 1 | Late-arriving events | `event_at < source_updated_at` | attribute to `event_at`; cursor on `source_updated_at` | `assert_late_events_backfilled` | ✅ |
| 2 | Duplicate events | `count(event_id) > 1` in bronze | dedup in staging | `assert_no_duplicate_events` | ✅ |
| 3 | Mutable CRM records | same `company_id`, rising `source_updated_at` | merge (upsert) at ingestion | `assert_lifecycle_transition` | ✅ |
| 4 | Late CRM updates | `source_updated_at` > creation | incremental pull on visibility | `assert_late_crm_update_applied` | ✅ |
| 5 | Future-effective records | `effective_at > recorded_at` | filter by effective date | `assert_future_effective_not_current` | ✅ |
| 6 | Standardisation | high dimension cardinality | staging maps to canonical | `assert_country_standardised`, `assert_plan_code_populated` | ✅ |
| 7 | Missing associations | null `company_id` | late-link CRM update | `assert_missing_association_resolved` | ✅ |
| 8 | Slowly-changing attributes | repeated keys with changing values | append-only history (SCD) | `assert_subscription_history_append_only` | ✅ |
| 9 | Schema evolution | `plan` present pre-cutover, `plan_code` post | dlt preserves unknown cols; dbt coalesce | `assert_plan_code_populated` | ✅ |

## Verification run

- Full clean-slate pipeline: `sim reset` → `sim history --days 90` → `dlt ingest` → `dbt build`.
- `dbt build`: **109/109 PASS** (25 models + 84 tests).
- All 8 DQ singular tests (covering the 9 scenarios) pass.

## Expected analytical results (verified)

- Late events land in the correct `event_at` day (activation/retention backfilled).
- Duplicate events do not inflate counts (`fct_product_events.event_id` unique).
- Churned companies are counted as churned, not `customer`.
- Late CRM updates are applied on their visible date.
- Future-effective changes do not appear in MRR before their effective month.
- Country/plan/frequency values are canonical (CA/GB/US; free/trial/pro/enterprise; monthly).
- Contacts gain their company association after the late link.
- Subscription history preserves superseded periods (expansion reconstructable).
- Every price resolves to a canonical `plan_code` regardless of schema era.
