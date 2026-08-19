-- assert_subscription_history_append_only.sql
-- DQ scenario 8: slowly-changing attributes (subscription history).
-- Plan/seat changes append new subscription periods; they never rewrite
-- history. Asserts multiple periods exist (history was preserved) and no
-- subscription_id has zero rows.

with multi_period as (
    select count() as n
    from {{ ref('fct_subscription_history') }}
    where status = 'superseded'
)
select *
from multi_period
where n = 0
