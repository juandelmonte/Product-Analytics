-- Monthly churn overview.
select
    month,
    active_at_start,
    churned_accounts,
    round(churn_rate, 4) as churn_rate
from marts.fct_churn
order by month
