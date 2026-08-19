-- assert_expansion_mrr_non_negative.sql
-- Business integrity: expansion MRR must be >= 0.

select *
from {{ ref('fct_account_mrr') }}
where expansion_mrr < 0
