-- Product behaviour of churned vs retained accounts (total usage).
with churned as (
    select distinct account_id
    from marts.fct_subscription_history
    where status = 'canceled'
),
usage as (
    select
        account_id,
        sum(total_events) as total_events,
        sum(active_days)  as active_days
    from marts.fct_usage_expansion
    group by account_id
)
select
    case when c.account_id is not null then 'churned' else 'retained' end as segment,
    countDistinct(u.account_id) as accounts,
    round(avg(u.total_events), 1) as avg_events,
    round(avg(u.active_days), 1)  as avg_active_days
from usage u
left join churned c on c.account_id = u.account_id
group by segment
