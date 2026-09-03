-- assert_churn_rate_bounded.sql
-- Analytical integrity: churn rate must be in [0, 1].

select *
from {{ ref('fct_churn') }}
where churn_rate > 1
   or churn_rate < 0
