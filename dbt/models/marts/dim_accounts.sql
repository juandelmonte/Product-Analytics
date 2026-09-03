-- dim_accounts.sql
-- Grain: one row per canonical account (SCD-current).
--
-- Conformed account dimension: the single source of truth for account
-- attributes. Joins the canonical identity to CRM company attributes and the
-- account's CURRENT plan (latest effective subscription).
--
-- This is a joinable star-schema dimension. Facts reference it by account_id;
-- they do not re-embed these attributes.

with current_plan as (
    select
        account_id,
        argMax(plan_code, effective_at) as plan_code
    from {{ ref('int_subscription_history') }}
    group by account_id
)

select
    i.account_id as account_id,
    i.company_id as company_id,
    i.customer_id as customer_id,
    c.name as name,
    c.industry as industry,
    c.company_size as company_size,
    c.country as country,
    c.lead_source as lead_source,
    c.lifecycle_stage as lifecycle_stage,
    cp.plan_code as plan_code,
    -- identity completeness flags (missing associations surfaced here)
    i.crm_identity_missing as crm_identity_missing,
    i.billing_identity_missing as billing_identity_missing
from {{ ref('int_identity_mapping') }} i
left join {{ ref('stg_crm_companies') }} c on c.company_id = i.company_id
left join current_plan cp on cp.account_id = i.account_id
