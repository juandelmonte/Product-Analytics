-- stg_billing_subscriptions.sql
-- Grain: one row per subscription period (append-only history).
-- Responsibility: preserve effective_at vs recorded_at (future-effective logic
-- lives downstream in int_subscription_history).

select
    subscription_id,
    customer_id,
    price_id,
    status,
    seats,
    start_date,
    ended_at,
    recorded_at,
    effective_at,
    source_updated_at
from {{ source('bronze', 'billing_subscriptions') }}
