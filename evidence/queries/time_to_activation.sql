-- Time-to-activation summary (days from signup to activation moment).
select
    round(quantile(0.25)(time_to_activation_days), 2) as p25_days,
    round(quantile(0.5)(time_to_activation_days), 2)  as p50_days,
    round(quantile(0.9)(time_to_activation_days), 2)  as p90_days,
    round(avg(time_to_activation_days), 2)            as avg_days,
    count()                                            as activated_accounts
from marts.fct_user_activation
where is_activated
