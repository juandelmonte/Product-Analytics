-- assert_activation_rate_bounded.sql
-- Analytical integrity: activation rate must be in [0, 1].

with cohort as (
    select signup_week, count(*) as total, countIf(is_activated) as activated
    from {{ ref('fct_user_activation') }}
    group by signup_week
)
select *
from cohort
where activated / total > 1
   or activated / total < 0
