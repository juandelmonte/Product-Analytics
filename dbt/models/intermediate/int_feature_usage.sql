-- int_feature_usage.sql
-- Grain: one row per account per feature per week.
--
-- Maps activity events to feature codes (per the event catalogue) and counts
-- usage per account, so feature adoption can be measured over a period.

with feature_events as (
    select
        account_id,
        event_at,
        case
            when event_name = 'workspace_created' then 'workspace'
            when event_name = 'project_created' then 'projects'
            when event_name in ('task_created', 'task_assigned', 'task_completed') then 'tasks'
            when event_name = 'task_commented' then 'comments'
            when event_name = 'integration_connected' then 'integrations'
        end as feature_code
    from {{ ref('stg_product_events') }}
    where event_name in (
        'workspace_created',
        'project_created',
        'task_created',
        'task_assigned',
        'task_completed',
        'task_commented',
        'integration_connected'
    )
)

select
    account_id,
    feature_code,
    toStartOfWeek(event_at) as usage_week,
    count(*) as event_count
from feature_events
where feature_code is not null
group by account_id, feature_code, usage_week
