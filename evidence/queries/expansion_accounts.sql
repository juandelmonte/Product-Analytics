-- Expanding accounts (account-months with positive expansion MRR).
select
    account_id,
    month,
    round(mrr, 2)            as mrr,
    round(expansion_mrr, 2)  as expansion_mrr,
    total_events,
    active_days
from marts.fct_usage_expansion
where is_expanding
order by month desc, expansion_mrr desc
