-- stg_crm_deals.sql
-- Grain: one row per deal (merge-disposed).

select
    deal_id,
    company_id,
    deal_stage,
    amount,
    toDate(close_date) as close_date,
    source_updated_at
from {{ source('bronze', 'crm_deals') }}
