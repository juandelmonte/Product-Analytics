-- Usage vs MRR, account-month grain (for scatter / correlation).
select
    account_id,
    month,
    total_events,
    active_days,
    round(mrr, 2)            as mrr,
    round(expansion_mrr, 2)  as expansion_mrr,
    is_expanding
from marts.fct_usage_expansion
order by month, account_id
