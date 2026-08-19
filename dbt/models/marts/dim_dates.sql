-- dim_dates.sql
-- Grain: one row per calendar day.
--
-- Date dimension covering the full history span, with grain attributes for
-- time-series slicing (year, quarter, month, week, day-of-week). Facts join on
-- date_key / day_date for calendar logic.

with bounds as (
    select
        min(toDate(event_at)) as min_d,
        max(toDate(event_at)) as max_d
    from {{ ref('stg_product_events') }}
),

spine as (
    select min_d + number as day_date
    from bounds
    array join range(toUInt32(max_d - min_d) + 1) as number
)

select
    day_date,
    toDate(day_date) as date_key,
    toYear(day_date) as year,
    toQuarter(day_date) as quarter,
    toMonth(day_date) as month,
    toStartOfWeek(day_date) as week_start,
    toDayOfWeek(day_date) as day_of_week,
    toDayOfMonth(day_date) as day_of_month
from spine
