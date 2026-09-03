-- fct_user_journey.sql
-- Grain: one row per account.
--
-- The canonical onboarding journey:
--   Signup → Workspace created → Project created → Teammate invited
--          → Task created → Task completed
-- Each step records the first event_at when the account reached it.

with first_events as (
    select
        account_id,
        minIf(event_at, event_name = 'account_created') as signup_at,
        minIf(event_at, event_name = 'workspace_created') as workspace_at,
        minIf(event_at, event_name = 'project_created') as project_at,
        minIf(event_at, event_name = 'membership_invited') as invite_at,
        minIf(event_at, event_name = 'task_created') as task_created_at,
        minIf(event_at, event_name = 'task_completed') as task_completed_at
    from {{ ref('stg_product_events') }}
    group by account_id
)

select
    account_id,
    signup_at,
    workspace_at,
    project_at,
    invite_at,
    task_created_at,
    task_completed_at,
    case when workspace_at is not null then true else false end as reached_workspace,
    case when project_at is not null then true else false end as reached_project,
    case when invite_at is not null then true else false end as reached_invite,
    case when task_created_at is not null then true else false end as reached_task_created,
    case when task_completed_at is not null then true else false end as reached_task_completed
from first_events
