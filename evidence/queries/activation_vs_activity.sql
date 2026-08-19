-- Activation status vs product activity (weeks active), answering
-- "are activated accounts more likely to remain active?".
with activity as (
    select
        account_id,
        countDistinct(toStartOfWeek(activity_date)) as active_weeks
    from marts.fct_user_daily_activity
    group by account_id
)
select
    a.account_id,
    a.is_activated,
    coalesce(ac.active_weeks, 0) as active_weeks
from marts.fct_user_activation a
left join activity ac on ac.account_id = a.account_id
