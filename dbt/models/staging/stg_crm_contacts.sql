-- stg_crm_contacts.sql
-- Grain: one row per contact (merge-disposed at source, so already deduped).

select
    contact_id,
    company_id,
    email,
    first_name,
    last_name,
    lifecycle_stage,
    source_updated_at
from {{ source('bronze', 'crm_contacts') }}
