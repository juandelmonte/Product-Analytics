-- int_identity_mapping.sql
-- Grain: one row per canonical account.
--
-- The canonical key is the product `account_id`. CRM (`company_id`) and billing
-- (`customer_id`) map to it via their `account_ref` linkage fields.

with product_accounts as (
    select distinct account_id
    from {{ ref('stg_product_events') }}
    where account_id is not null
),

crm_map as (
    select
        account_ref as account_id,
        company_id
    from {{ ref('stg_crm_companies') }}
    where account_ref is not null
),

billing_map as (
    select
        account_ref as account_id,
        customer_id
    from {{ ref('stg_billing_customers') }}
    where account_ref is not null
)

select
    pa.account_id as account_id,
    c.company_id as company_id,
    b.customer_id as customer_id,
    -- identity completeness flags (missing associations surfaced here)
    case when c.company_id is null then true else false end as crm_identity_missing,
    case when b.customer_id is null then true else false end as billing_identity_missing
from product_accounts pa
left join crm_map c on c.account_id = pa.account_id
left join billing_map b on b.account_id = pa.account_id
