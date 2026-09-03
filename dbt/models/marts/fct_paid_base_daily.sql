-- fct_paid_base_daily.sql
-- Grain: one row per calendar day.
--
-- Daily evolution of the paid base. A paid period is a subscription whose
-- plan_code is 'pro' or 'enterprise'.
--   cum_converted : accounts that have EVER had a paid period, counted from the
--                   day of their first paid start.
--   cum_churned   : paid accounts whose subscription ended with status
--                   'canceled', counted from the day it ended.
--   paid_accounts : cum_converted - cum_churned = accounts currently on a paid
--                   plan (a running, zero-filled daily view).
--
-- Note: this is a BILLING view of "active" (currently paying), not a usage
-- (event) view. It complements DAU/WAU rather than replacing it.

with paid_periods as (
    select
        account_id,
        toDate(start_date) as start_date,
        toDate(ended_at)   as ended_at,
        status
    from {{ ref('fct_subscription_history') }}
    where plan_code in ('pro', 'enterprise')
),

first_paid as (
    select account_id, min(start_date) as first_paid_at
    from paid_periods
    group by account_id
),

last_churn as (
    select account_id, max(ended_at) as churned_at
    from paid_periods
    where status = 'canceled' and ended_at is not null
    group by account_id
),

-- per-day event counts (a day may have 0 of either)
conv_days as (
    select first_paid_at as day_date, count() as n_conv
    from first_paid
    group by first_paid_at
),

churn_days as (
    select churned_at as day_date, count() as n_churn
    from last_churn
    group by churned_at
),

-- full calendar between the first paid start and the latest paid start/churn
bounds as (
    select
        min(first_paid_at) as min_d,
        max(greatest(first_paid_at, coalesce(churned_at, first_paid_at))) as max_d
    from first_paid
    left join last_churn using (account_id)
),

calendar as (
    select min_d + number as day_date
    from bounds
    array join range(toUInt32(max_d - min_d) + 1) as number
),

daily as (
    select
        c.day_date as day_date,
        coalesce(cv.n_conv, 0)  as n_conv,
        coalesce(ch.n_churn, 0) as n_churn
    from calendar c
    left join conv_days cv on cv.day_date = c.day_date
    left join churn_days ch on ch.day_date = c.day_date
)

select
    day_date,
    sum(n_conv)  over (order by day_date) as cum_converted,
    sum(n_churn) over (order by day_date) as cum_churned,
    sum(n_conv)  over (order by day_date) - sum(n_churn) over (order by day_date) as paid_accounts
from daily
order by day_date
