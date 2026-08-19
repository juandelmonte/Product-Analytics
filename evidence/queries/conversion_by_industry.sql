-- Paid conversion rate by industry (star join).
select
    d.industry as industry,
    count() as accounts,
    countIf(c.is_converted) as converted,
    round(countIf(c.is_converted) / count(), 4) as conversion_rate
from marts.fct_paid_conversion c
join marts.dim_accounts d on d.account_id = c.account_id
group by d.industry
order by d.industry
