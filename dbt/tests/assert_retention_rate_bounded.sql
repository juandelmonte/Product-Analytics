-- assert_retention_rate_bounded.sql
-- Analytical integrity: retention rate must be in [0, 1].

select *
from {{ ref('fct_retention') }}
where retention_rate > 1
   or retention_rate < 0
