-- assert_activation_within_window.sql
-- Business integrity: an activated account must activate within 7 days.

select *
from {{ ref('fct_user_activation') }}
where is_activated = true
  and time_to_activation_days > 7
