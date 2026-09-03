-- Onboarding funnel: distinct accounts reaching each step, in journey order.
-- Ordered by step_number so BI layers render the funnel top-to-bottom.
select
    step_number,
    step,
    accounts
from (
    select 1 as step_number, 'Signup'                  as step, count() as accounts from marts.fct_user_journey
    union all
    select 2, 'Workspace created', countIf(reached_workspace)      from marts.fct_user_journey
    union all
    select 3, 'Project created',   countIf(reached_project)        from marts.fct_user_journey
    union all
    select 4, 'Teammate invited',  countIf(reached_invite)         from marts.fct_user_journey
    union all
    select 5, 'Task created',      countIf(reached_task_created)   from marts.fct_user_journey
    union all
    select 6, 'Task completed',    countIf(reached_task_completed) from marts.fct_user_journey
)
order by step_number
