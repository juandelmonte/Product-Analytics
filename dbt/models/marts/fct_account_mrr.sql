-- fct_account_mrr.sql
-- Grain: one row per account per month.
--
-- MRR = sum(seats × monthly_unit_amount) over subscriptions active in the month.
-- A subscription contributes to EVERY month it is live (from effective month
-- through the month before it ends), not just its start month.
--
-- Expansion MRR = positive month-over-month MRR change for accounts already
-- paying in the prior month.

with subs as (
    select
        account_id,
        subscription_id,
        plan_code,
        status,
        seats,
        monthly_unit_amount,
        effective_at,
        ended_at
    from {{ ref('int_subscription_history') }}
),

-- expand each subscription over the months it was live. A row contributes MRR
-- during its [effective_at, ended_at) interval, regardless of its CURRENT
-- status (append-only history: superseded rows were live before their successor
-- took effect).
month_spine as (
    select
        account_id,
        subscription_id,
        seats,
        monthly_unit_amount,
        toStartOfMonth(effective_at) as start_month,
        toStartOfMonth(coalesce(ended_at, toDate(now()))) as end_month
    from subs
    where monthly_unit_amount > 0
      and seats > 0
),

monthly_mrr as (
    select
        account_id,
        toStartOfMonth(addMonths(ms.start_month, m)) as mrr_month,
        sum(ms.seats * ms.monthly_unit_amount) as mrr
    from month_spine ms
    array join
        range(0, toInt32(dateDiff('month', ms.start_month, ms.end_month)) + 1) as m
    group by account_id, mrr_month
)

select
    account_id,
    mrr_month,
    mrr,
    -- expansion MRR: positive MoM change for accounts paying last month
    greatest(
        mrr - lagInFrame(mrr, 1, mrr) over (
            partition by account_id
            order by mrr_month
        ),
        0
    ) as expansion_mrr
from monthly_mrr
