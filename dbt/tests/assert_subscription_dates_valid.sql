-- assert_subscription_dates_valid.sql
-- Business integrity: ended_at (when set) must be >= start_date.

select *
from {{ ref('fct_subscription_history') }}
where ended_at is not null
  and ended_at < start_date
