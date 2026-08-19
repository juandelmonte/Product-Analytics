-- Activation rate by signup week.
select
    signup_week as cohort,
    count() as accounts,
    countIf(is_activated) as activated,
    round(countIf(is_activated) / count(), 4) as activation_rate
from marts.fct_user_activation
group by signup_week
order by signup_week
