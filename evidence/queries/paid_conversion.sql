-- Paid conversion rate overall and split by activation status.
select
    a.is_activated,
    count() as accounts,
    countIf(c.is_converted) as converted,
    round(countIf(c.is_converted) / count(), 4) as conversion_rate
from marts.fct_paid_conversion c
left join marts.fct_user_activation a on a.account_id = c.account_id
group by a.is_activated
order by a.is_activated
