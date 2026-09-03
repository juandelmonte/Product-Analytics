-- Star-schema join demo: activation rate sliced by account country/plan.
-- Joins the fact (fct_user_activation) to the conformed dim (dim_accounts),
-- showing how a fact is sliced by dimension attributes at query time.
select
    d.country,
    d.plan_code,
    count() as accounts,
    countIf(f.is_activated) as activated,
    round(countIf(f.is_activated) / count(), 4) as activation_rate
from marts.fct_user_activation f
join marts.dim_accounts d on d.account_id = f.account_id
group by d.country, d.plan_code
order by d.country, d.plan_code
