-- Monthly MRR and expansion MRR.
select
    mrr_month,
    round(sum(mrr), 2)            as total_mrr,
    countDistinct(account_id)     as paying_accounts,
    round(sum(expansion_mrr), 2)  as expansion_mrr
from marts.fct_account_mrr
group by mrr_month
order by mrr_month
