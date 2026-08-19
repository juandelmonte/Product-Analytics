-- Distribution of time-to-activation (days).
select
    time_to_activation_days,
    count() as accounts
from marts.fct_user_activation
where is_activated
group by time_to_activation_days
order by time_to_activation_days
