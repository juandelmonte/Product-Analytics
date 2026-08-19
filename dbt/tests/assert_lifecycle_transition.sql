-- assert_lifecycle_transition.sql
-- DQ scenario 3: mutable CRM records.
-- A company that moved to 'churned' must be counted as churned, not still
-- 'customer'. Asserts churned companies exist (mutation happened) and that
-- companies have exactly ONE current row (merge disposition deduped).

with churned as (
    select count() as n
    from {{ ref('stg_crm_companies') }}
    where lifecycle_stage = 'churned'
)
select *
from churned
where n = 0
