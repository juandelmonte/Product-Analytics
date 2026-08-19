-- stg_crm_companies.sql
-- Grain: one row per company (merge-disposed).
-- Responsibility: standardise country / company_size / lifecycle values.

select
    company_id,
    account_ref,
    name,
    industry,
    company_size,
    {{ standardise_country('country') }} as country,
    lead_source,
    lifecycle_stage,
    source_updated_at
from {{ source('bronze', 'crm_companies') }}
