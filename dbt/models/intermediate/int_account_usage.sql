-- int_account_usage.sql
-- Grain: one row per account per month.
--
-- Monthly product usage intensity: total activity events + distinct features
-- used. Drives the usage → expansion correlation and pre-churn behaviour.

select
    account_id,
    toStartOfMonth(activity_date) as usage_month,
    sum(event_count) as total_events,
    sum(distinct_features) as feature_touches,
    count(distinct activity_date) as active_days
from {{ ref('int_user_activity') }}
group by account_id, usage_month
