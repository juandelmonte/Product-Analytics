-- dim_plans.sql
-- Grain: one row per plan (the billing price catalog, canonicalised).
--
-- Plan dimension: plan_code, seat price, and billing frequency. Facts that
-- involve plan-level attributes (e.g. MRR normalisation) join to this instead
-- of re-embedding unit_amount / billing_frequency.

select
    price_id,
    plan_code,
    unit_amount,
    billing_frequency
from {{ ref('stg_billing_prices') }}
