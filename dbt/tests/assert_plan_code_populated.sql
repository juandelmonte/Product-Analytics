-- assert_plan_code_populated.sql
-- DQ scenario 9: schema evolution (plan → plan_code) + standardisation.
-- Every price must resolve to a canonical plan_code, whether it came from the
-- pre-cutover `plan` column or the post-cutover `plan_code` column.

select *
from {{ ref('stg_billing_prices') }}
where plan_code is null
   or plan_code not in ('free', 'trial', 'pro', 'enterprise')
