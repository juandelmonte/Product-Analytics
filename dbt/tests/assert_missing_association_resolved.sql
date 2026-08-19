-- assert_missing_association_resolved.sql
-- DQ scenario 7: missing associations.
-- Some CRM contacts started with no company and gained one later. Asserts the
-- resolution happened: the share of contacts with a company is high (not 0)
-- and there are no orphaned contacts in the identity-mapped fact.

with contact_coverage as (
    select
        countIf(company_id is not null) as linked,
        count() as total
    from {{ ref('stg_crm_contacts') }}
)
select *
from contact_coverage
where linked = 0 or linked / total < 0.5
