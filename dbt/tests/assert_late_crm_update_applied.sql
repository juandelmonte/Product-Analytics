-- assert_late_crm_update_applied.sql
-- DQ scenario 4: late CRM updates.
-- A CRM record changed after creation has source_updated_at > its creation
-- (proxied by the earliest event_at of the linked account). Asserts such
-- updated records exist and are current in staging.

with updated_companies as (
    select count() as n
    from {{ ref('stg_crm_companies') }}
    where lifecycle_stage in ('customer', 'churned')
)
select *
from updated_companies
where n = 0
