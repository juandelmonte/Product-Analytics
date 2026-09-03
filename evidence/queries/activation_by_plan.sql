-- Activation rate by plan (star join: fct_user_activation ⋈ dim_accounts).
select
    d.plan_code as plan,
    count() as accounts,
    countIf(f.is_activated) as activated,
    round(countIf(f.is_activated) / count(), 4) as activation_rate
from marts.fct_user_activation f
join marts.dim_accounts d on d.account_id = f.account_id
group by d.plan_code
order by d.plan_code
