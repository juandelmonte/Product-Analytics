-- assert_activation_after_signup.sql
-- Business integrity: activation can never precede signup.

select *
from {{ ref('fct_user_activation') }}
where is_activated = true
  and activation_at < signup_at
