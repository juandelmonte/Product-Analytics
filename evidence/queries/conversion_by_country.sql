-- Paid conversion rate by country (star join).
select
    d.country as country,
    count() as accounts,
    countIf(c.is_converted) as converted,
    round(countIf(c.is_converted) / count(), 4) as conversion_rate
from marts.fct_paid_conversion c
join marts.dim_accounts d on d.account_id = c.account_id
group by d.country
order by d.country
