-- assert_no_duplicate_events.sql
-- DQ scenario 2: duplicate events.
-- A client retry re-delivers the same event_id. Bronze keeps both; staging
-- dedups. The fact must have a unique event_id.

select
    event_id,
    count(*) as n
from {{ ref('fct_product_events') }}
group by event_id
having count(*) > 1
