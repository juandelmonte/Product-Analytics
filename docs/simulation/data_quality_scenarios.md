# Data Quality Scenarios

Nine deliberate, realistic source-quality problems are baked into the
simulation. Each documents: **Source behaviour → Detection → Treatment → Test →
Expected analytical result**.

| # | Scenario | Source behaviour |
|---|----------|------------------|
| 1 | Late-arriving events | event delivered days after `event_at` |
| 2 | Duplicate events | same `event_id` delivered twice |
| 3 | Mutable CRM records | `company_size`, `industry`, `lifecycle_stage`, `lead_source` change |
| 4 | Late CRM updates | a CRM change is only visible days later |
| 5 | Future-effective records | billing `recorded_at` < `effective_at` |
| 6 | Standardisation | `US/USA/United States`, `Enterprise/ENT`, `Monthly/month` |
| 7 | Missing associations | a contact starts with no company, gains one later |
| 8 | Slowly-changing attributes | account plan/industry changes over time |
| 9 | Schema evolution | `plan` later becomes `plan` + `plan_code` |

---

## 1. Late-arriving events

- **Source behaviour**: a `product_event` has `event_at` in the past but is only
  served by the API on a later day (its `source_updated_at`/delivery date lags).
- **Detection**: `event_at != source_updated_at` (large gap) in bronze; ingestion
  watermark on `source_updated_at` means late rows are picked up on a later run.
- **Treatment**: analytics always attribute to `event_at`; ingestion diagnostics
  use `ingested_at`. Incremental dlt must cursor on `source_updated_at`, not
  `event_at`, so late events are not skipped.
- **Test**: `assert_late_events_backfilled` — a late event lands in the correct
  day bucket in marts.
- **Expected result**: activation/retention for a past day updates after the
  late event arrives.

## 2. Duplicate events

- **Source behaviour**: a client retry re-delivers an event with the same
  `event_id`.
- **Detection**: `count(event_id) > 1` in bronze.
- **Treatment**: deduplicate in dbt staging on `event_id` (keep first by
  `source_updated_at`).
- **Test**: `assert_no_duplicate_events` — `fct_product_events` has unique
  `event_id`.
- **Expected result**: metric counts are not inflated by retries.

## 3. Mutable CRM records

- **Source behaviour**: a CRM company's `industry`, `company_size`,
  `lifecycle_stage`, or `lead_source` is updated after creation.
- **Detection**: rows with the same `company_id` and increasing
  `source_updated_at`.
- **Treatment**: SCD2 in dbt (keep the current value for point-in-time views;
  preserve history where required).
- **Test**: `assert_lifecycle_transition` — a company that moved to `churned`
  is counted as churned, not still `customer`.
- **Expected result**: churn/segmentation reflects the latest values.

## 4. Late CRM updates

- **Source behaviour**: a CRM change is recorded but only becomes available in
  the export days later.
- **Detection**: `source_updated_at` (export time) > the moment the business
  change actually happened.
- **Treatment**: incremental dlt pulls the update on the day it becomes visible;
  dbt applies it from that point.
- **Test**: `assert_late_crm_update_applied`.
- **Expected result**: late CRM changes are applied on their visible date.

## 5. Future-effective records

- **Source behaviour**: billing `recorded_at = Aug 20`, `effective_at = Sep 1`.
- **Detection**: `effective_at > recorded_at` in bronze.
- **Treatment**: never treat a future-effective change as current until
  `effective_at <= run date`; dbt filters on effective date.
- **Test**: `assert_future_effective_not_current`.
- **Expected result**: MRR changes land in the effective month, not the
  recorded month.

## 6. Standardisation

- **Source behaviour**: free-text variants: `US/USA/United States`,
  `Enterprise/enterprise/ENT`, `Monthly/monthly/month`.
- **Detection**: cardinality of a dimension is unexpectedly high.
- **Treatment**: dbt staging maps variants to canonical codes (country ISO2,
  plan code, frequency).
- **Test**: `assert_country_standardised`, `assert_plan_standardised`.
- **Expected result**: dimensions join cleanly and aggregate correctly.

## 7. Missing associations

- **Source behaviour**: a CRM contact has `company_id = null` at creation and
  is linked later.
- **Detection**: null `company_id` on contacts.
- **Treatment**: identity mapping leaves it unresolved until linked; the
  late-link path updates it.
- **Test**: `assert_missing_association_resolved`.
- **Expected result**: contact counts per company are correct after linking.

## 8. Slowly-changing attributes

- **Source behaviour**: account plan (trial→pro) and industry change over time.
- **Detection**: repeated keys with different values.
- **Treatment**: billing subscriptions are append-only (history preserved);
  CRM attributes are SCD2.
- **Test**: `assert_subscription_history_append_only`.
- **Expected result**: point-in-time MRR is reconstructable.

## 9. Schema evolution

- **Source behaviour**: before a cutover, `billing_prices` has only `plan`
  (`"Pro"`); after, it has `plan` **and** `plan_code` (`"pro"`).
- **Detection**: columns present only for some rows.
- **Treatment**: dlt preserves unknown columns; dbt staging coalesces
  `plan_code = coalesce(plan_code, standardise(plan))`.
- **Test**: `assert_plan_code_populated` — every price has a canonical
  `plan_code` regardless of era.
- **Expected result**: MRR and adoption are unaffected by the schema change.
