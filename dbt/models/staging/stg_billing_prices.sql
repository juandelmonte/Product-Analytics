-- stg_billing_prices.sql
-- Grain: one row per price (merge-disposed).
-- Responsibility: schema evolution - coalesce plan_code from plan, standardise
-- the billing frequency.

select
    price_id,
    product_id,
    -- schema evolution: before the cutover only `plan` (messy) exists;
    -- after, `plan_code` is authoritative.
    coalesce(
        {{ standardise_plan('plan_code') }},
        {{ standardise_plan('plan') }}
    ) as plan_code,
    unit_amount,
    currency,
    {{ standardise_frequency('billing_frequency') }} as billing_frequency,
    source_updated_at
from {{ source('bronze', 'billing_prices') }}
