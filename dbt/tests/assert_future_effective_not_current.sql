-- assert_future_effective_not_current.sql
-- DQ scenario: future-effective changes must not be attributed to a month
-- before they take effect. No MRR row may carry a future month.

select *
from {{ ref('fct_account_mrr') }}
where mrr_month > toStartOfMonth(now())
