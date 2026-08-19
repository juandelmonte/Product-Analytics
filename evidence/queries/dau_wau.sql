-- DAU / WAU / stickiness over time.
--
-- DAU = distinct users active on the day.
-- WAU = distinct users active in the trailing 7 days (including the day).
-- stickiness = DAU / WAU (share of the weekly audience active on a given day).
--
-- Memory-safe: each (user, day) "covers" the next 7 days; WAU for a day is the
-- distinct users whose activity falls in [day-6, day]. No cross join, no window
-- INTERVAL frame (unsupported in ClickHouse).
with user_days as (
    select distinct
        user_id,
        activity_date
    from marts.fct_user_daily_activity
),
dau as (
    select
        activity_date,
        count() as dau
    from user_days
    group by activity_date
),
wau as (
    select
        activity_date + offset as activity_date,
        countDistinct(user_id) as wau
    from user_days
    array join range(7) as offset
    group by activity_date
)
select
    d.activity_date as activity_date,
    d.dau,
    w.wau,
    round(d.dau / w.wau, 4) as stickiness
from dau d
join wau w on w.activity_date = d.activity_date
order by d.activity_date


