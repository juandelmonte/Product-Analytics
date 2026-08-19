-- int_user_activity.sql
-- Grain: one row per user per day with product activity.
--
-- Activity events (per the event catalogue) feed DAU/WAU, retention, and
-- feature adoption downstream.

with activity_events as (
    select
        distinct_id as user_id,
        account_id,
        toDate(event_at) as activity_date,
        event_name
    from {{ ref('stg_product_events') }}
    where event_name in (
        'workspace_created',
        'project_created',
        'task_created',
        'task_assigned',
        'task_commented',
        'task_completed',
        'integration_connected'
    )
)

select
    user_id,
    account_id,
    activity_date,
    count(*) as event_count,
    count(distinct event_name) as distinct_features
from activity_events
group by user_id, account_id, activity_date
