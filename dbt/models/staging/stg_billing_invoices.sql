-- stg_billing_invoices.sql
-- Grain: one row per invoice (merge-disposed).

select
    invoice_id,
    customer_id,
    subscription_id,
    amount_due,
    status,
    created_at,
    source_updated_at
from {{ source('bronze', 'billing_invoices') }}
