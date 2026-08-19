-- Activation rate by company size (star join).
select
    d.company_size as company_size,
    count() as accounts,
    countIf(f.is_activated) as activated,
    round(countIf(f.is_activated) / count(), 4) as activation_rate
from marts.fct_user_activation f
join marts.dim_accounts d on d.account_id = f.account_id
group by d.company_size
order by d.company_size
