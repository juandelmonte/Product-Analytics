-- fct_usage_expansion.sql
-- Grain: one row per account per month.
--
-- Links product usage to MRR and expansion. Answers "how does product usage
-- relate to MRR?" and "which accounts expand?".

with usage as (
    select
        account_id,
        usage_month,
        total_events,
        feature_touches,
        active_days
    from {{ ref('int_account_usage') }}
),

mrr as (
    select
        account_id,
        mrr_month,
        mrr,
        expansion_mrr
    from {{ ref('fct_account_mrr') }}
)

select
    coalesce(u.account_id, m.account_id) as account_id,
    coalesce(u.usage_month, m.mrr_month) as month,
    coalesce(u.total_events, 0) as total_events,
    coalesce(u.feature_touches, 0) as feature_touches,
    coalesce(u.active_days, 0) as active_days,
    coalesce(m.mrr, 0) as mrr,
    coalesce(m.expansion_mrr, 0) as expansion_mrr,
    case when m.expansion_mrr > 0 then true else false end as is_expanding
from usage u
full outer join mrr m
    on m.account_id = u.account_id
   and m.mrr_month = u.usage_month
