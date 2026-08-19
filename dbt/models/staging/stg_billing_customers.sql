-- stg_billing_customers.sql
-- Grain: one row per billing customer (merge-disposed).

select
    customer_id,
    account_ref,
    email,
    name,
    source_updated_at
from {{ source('bronze', 'billing_customers') }}
