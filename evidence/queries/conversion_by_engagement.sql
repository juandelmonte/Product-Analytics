-- Paid conversion by engagement segment (total product events per account).
with usage as (
    select account_id, count() as total_events
    from marts.fct_product_events
    group by account_id
)
select
    case
        when u.total_events < 10  then 'low'
        when u.total_events < 50  then 'medium'
        else 'high'
    end as engagement_segment,
    count() as accounts,
    countIf(c.is_converted) as converted,
    round(countIf(c.is_converted) / count(), 4) as conversion_rate
from marts.fct_paid_conversion c
left join usage u on u.account_id = c.account_id
group by engagement_segment
order by engagement_segment
