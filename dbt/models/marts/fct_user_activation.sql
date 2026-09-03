-- fct_user_activation.sql
-- Grain: one row per account (signup cohort anchor).
--
-- Exposes activation rate (share of new accounts activated) and time-to-activation.

select
    account_id,
    signup_at,
    workspace_at,
    project_at,
    invite_at,
    task_done_at,
    activation_at,
    is_activated,
    time_to_activation_days,
    -- signup week/month cohort keys
    toStartOfWeek(signup_at) as signup_week,
    toStartOfMonth(signup_at) as signup_month
from {{ ref('int_user_activation') }}
