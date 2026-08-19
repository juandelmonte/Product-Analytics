-- assert_feature_adoption_rate_bounded.sql
-- Analytical integrity: adoption rate must be in [0, 1].

select *
from {{ ref('fct_feature_adoption') }}
where adoption_rate > 1
   or adoption_rate < 0
