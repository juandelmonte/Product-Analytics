-- assert_mrr_non_negative.sql
-- Business integrity: MRR must be >= 0.

select *
from {{ ref('fct_account_mrr') }}
where mrr < 0
