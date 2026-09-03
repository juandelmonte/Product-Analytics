-- fct_product_events.sql
-- Grain: one row per unique event.
--
-- The business-ready fact of every product event, joined to the canonical
-- identity mapping (so CRM/billing ids are available alongside the product id).

select
    e.event_id,
    e.event_name,
    e.distinct_id as user_id,
    e.account_id,
    e.event_at,
    e.source_updated_at,
    e.country,
    e.channel,
    e.workspace_id,
    e.project_id,
    e.task_id,
    e.integration_type,
    e.from_plan,
    e.to_plan,
    i.company_id,
    i.customer_id
from {{ ref('stg_product_events') }} e
left join {{ ref('int_identity_mapping') }} i on i.account_id = e.account_id
