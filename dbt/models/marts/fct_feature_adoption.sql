-- fct_feature_adoption.sql
-- Grain: one row per feature per week.
--
-- Feature adoption rate = share of active accounts that used a feature at least
-- once in the period. "Active accounts" = accounts with any activity event in
-- the same week.

with active_accounts as (
    select distinct
        account_id,
        toStartOfWeek(activity_date) as activity_week
    from {{ ref('int_user_activity') }}
)

select
    f.feature_code,
    f.usage_week as week,
    count(distinct f.account_id) as accounts_using_feature,
    count(distinct aa.account_id) as active_accounts,
    count(distinct f.account_id) / nullif(count(distinct aa.account_id), 0) as adoption_rate
from {{ ref('int_feature_usage') }} f
left join active_accounts aa
    on aa.activity_week = f.usage_week
group by f.feature_code, f.usage_week
