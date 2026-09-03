-- stg_product_events.sql
-- Grain: one row per unique event_id (deduplicated).
--
-- Responsibilities:
--   1. Deduplicate on event_id (DQ scenario: duplicate events).
--   2. Flatten common event properties into typed columns.
--   3. Preserve event_at (business time) and source_updated_at (ingestion time).

{{ config(materialized='table') }}

with deduped as (
    select
        *,
        row_number() over (
            partition by event_id
            order by source_updated_at asc, _dlt_load_id asc
        ) as rn
    from {{ source('bronze', 'product_events') }}
)

select
    event_id,
    event_name,
    distinct_id,
    account_id,
    event_at,
    source_updated_at,
    -- common flattened properties
    toString(properties__country) as country,
    toString(properties__channel) as channel,
    toString(properties__workspace_id) as workspace_id,
    toString(properties__project_id) as project_id,
    toString(properties__task_id) as task_id,
    toString(properties__integration_type) as integration_type,
    toString(properties__from_plan) as from_plan,
    toString(properties__to_plan) as to_plan
from deduped
where rn = 1
