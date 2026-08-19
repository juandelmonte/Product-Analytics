-- fct_user_daily_activity.sql
-- Grain: one row per user per day.
--
-- Daily active users (DAU) are the distinct users with >=1 activity event on a
-- day. WAU is derivable by aggregating to a trailing 7-day window.

select
    user_id,
    account_id,
    activity_date,
    event_count,
    distinct_features,
    -- active flag (DAU definition: any activity event on the day)
    case when event_count > 0 then true else false end as is_active
from {{ ref('int_user_activity') }}
