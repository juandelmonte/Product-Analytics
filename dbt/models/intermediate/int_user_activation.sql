-- int_user_activation.sql
-- Grain: one row per account.
--
-- Activation definition (locked in docs/business/business_case.md): an account is activated
-- when, within 7 days of signup, it has:
--   1. created a workspace
--   2. created a project
--   3. invited a teammate (membership_invited)
--   4. completed a task
--
-- The activation moment is the LATEST of the four signals.

with signups as (
    select
        account_id,
        min(event_at) as signup_at
    from {{ ref('stg_product_events') }}
    where event_name = 'account_created'
    group by account_id
),

signals as (
    select
        e.account_id,
        max(case when e.event_name = 'workspace_created' then e.event_at end) as workspace_at,
        max(case when e.event_name = 'project_created' then e.event_at end) as project_at,
        max(case when e.event_name = 'membership_invited' then e.event_at end) as invite_at,
        max(case when e.event_name = 'task_completed' then e.event_at end) as task_done_at
    from {{ ref('stg_product_events') }} e
    join signups s on s.account_id = e.account_id
    where e.event_name in ('workspace_created', 'project_created', 'membership_invited', 'task_completed')
      -- constrain to the activation window (7 days from signup)
      and e.event_at <= s.signup_at + interval 7 day
    group by e.account_id
)

select
    s.account_id,
    s.signup_at,
    sig.workspace_at,
    sig.project_at,
    sig.invite_at,
    sig.task_done_at,
    -- the latest of the four signals, only meaningful when all are present
    greatest(
        coalesce(sig.workspace_at, toDateTime('1970-01-01')),
        coalesce(sig.project_at, toDateTime('1970-01-01')),
        coalesce(sig.invite_at, toDateTime('1970-01-01')),
        coalesce(sig.task_done_at, toDateTime('1970-01-01'))
    ) as activation_at,
    -- all four signals must be present AND within 7 days of signup
    case
        when sig.workspace_at is not null
         and sig.project_at is not null
         and sig.invite_at is not null
         and sig.task_done_at is not null
         and greatest(
             sig.workspace_at, sig.project_at, sig.invite_at, sig.task_done_at
         ) <= s.signup_at + interval 7 day
        then true
        else false
    end as is_activated,
    dateDiff('day', s.signup_at,
        greatest(
            coalesce(sig.workspace_at, toDateTime('1970-01-01')),
            coalesce(sig.project_at, toDateTime('1970-01-01')),
            coalesce(sig.invite_at, toDateTime('1970-01-01')),
            coalesce(sig.task_done_at, toDateTime('1970-01-01'))
        )
    ) as time_to_activation_days
from signups s
left join signals sig on sig.account_id = s.account_id
