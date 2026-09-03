-- int_subscription_history.sql
-- Grain: one row per subscription period (append-only history preserved).
--
-- Responsibilities:
--   1. Join each subscription to its price (plan_code, unit_amount, frequency).
--   2. Join to the canonical identity (account_id via customer.account_ref).
--   3. Preserve effective_at vs recorded_at so future-effective changes are
--      not treated as current (downstream filters on effective_at <= run date).

with subs as (
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
    from {{ ref('stg_billing_subscriptions') }}
),

prices as (
    select
        price_id,
        plan_code,
        unit_amount,
        billing_frequency
    from {{ ref('stg_billing_prices') }}
),

customers as (
    select
        customer_id,
        account_ref as account_id
    from {{ ref('stg_billing_customers') }}
)

select
    s.subscription_id as subscription_id,
    s.customer_id as customer_id,
    c.account_id as account_id,
    s.price_id as price_id,
    p.plan_code as plan_code,
    s.status as status,
    s.seats as seats,
    p.unit_amount as unit_amount,
    p.billing_frequency as billing_frequency,
    -- normalise the seat price to a monthly unit
    case
        when p.billing_frequency = 'annual' then p.unit_amount / 12.0
        else p.unit_amount
    end as monthly_unit_amount,
    s.start_date as start_date,
    s.ended_at as ended_at,
    s.recorded_at as recorded_at,
    s.effective_at as effective_at,
    s.source_updated_at as source_updated_at
from subs s
left join prices p on p.price_id = s.price_id
left join customers c on c.customer_id = s.customer_id
