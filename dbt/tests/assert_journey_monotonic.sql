-- assert_journey_monotonic.sql
-- Analytical integrity: journey step reach must be monotonic (a later step
-- cannot be reached if an earlier one is not).

select *
from {{ ref('fct_user_journey') }}
where (reached_project and not reached_workspace)
   or (reached_task_created and not reached_project)
   or (reached_task_completed and not reached_task_created)
