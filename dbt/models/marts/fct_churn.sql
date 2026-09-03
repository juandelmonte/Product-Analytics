-- fct_churn.sql
-- Grain: one row per account per month.
--
-- Churn: an account churns in a month if its active subscription ends in that
-- month (status becomes canceled). Churn rate = churned accounts / accounts with
-- an active subscription at month start.

with subs as (
    select
        account_id,
        subscription_id,
        status,
        start_date,
        ended_at,
        toStartOfMonth(effective_at) as effective_month
    from {{ ref('int_subscription_history') }}
),

-- accounts with an active subscription at the start of each month
active_at_month_start as (
    select distinct
        account_id,
        effective_month as month
    from subs
    where status in ('active', 'trialing', 'past_due')
),

-- accounts whose subscription ended in a given month
churned as (
    select distinct
        account_id,
        toStartOfMonth(ended_at) as month
    from subs
    where status = 'canceled'
      and ended_at is not null
)

select
    a.month,
    count(distinct a.account_id) as active_at_start,
    count(distinct c.account_id) as churned_accounts,
    count(distinct c.account_id) / nullif(count(distinct a.account_id), 0) as churn_rate
from active_at_month_start a
left join churned c
    on c.account_id = a.account_id
   and c.month = a.month
group by a.month
