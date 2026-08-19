-- fct_subscription_history.sql
-- Grain: one row per subscription period.
--
-- Business-facing subscription history (fact). A change (plan/seat) appends a
-- new period; this table preserves the full timeline so MRR can be
-- reconstructed point-in-time.
--
-- Plan-level attributes (unit_amount, billing_frequency) live in dim_plans and
-- are joined via price_id/plan_code, not re-embedded here.

select
    subscription_id,
    customer_id,
    account_id,
    price_id,
    plan_code,
    status,
    seats,
    start_date,
    ended_at,
    recorded_at,
    effective_at,
    source_updated_at
from {{ ref('int_subscription_history') }}
