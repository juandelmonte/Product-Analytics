-- Activation rate by industry (star join).
select
    d.industry as industry,
    count() as accounts,
    countIf(f.is_activated) as activated,
    round(countIf(f.is_activated) / count(), 4) as activation_rate
from marts.fct_user_activation f
join marts.dim_accounts d on d.account_id = f.account_id
group by d.industry
order by d.industry
