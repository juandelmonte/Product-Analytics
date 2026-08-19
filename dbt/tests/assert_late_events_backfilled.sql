-- assert_late_events_backfilled.sql
-- DQ scenario 1: late-arriving events.
-- A late event has event_at (business time) strictly before its source_updated_at
-- (when it became available). It must still be attributed to its event_at day
-- in the product events fact. This asserts late events EXIST and are preserved.

with late_events as (
    select count() as n
    from {{ ref('fct_product_events') }}
    where event_at < source_updated_at - interval 1 hour
)
select *
from late_events
where n = 0
