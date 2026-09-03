-- fct_retention.sql
-- Grain: one row per cohort × week offset.
--
-- Weekly retention: share of a signup cohort still active N weeks after signup.
-- Cohort = signup week; "active in week N" = any activity event in that calendar
-- week. Activated-cohort comparison is possible by joining to fct_user_activation.
--
-- RIGHT-CENSORING: a cohort's observable window ends at the latest activity week
-- in the data. We only emit offsets up to that horizon per cohort, so recent
-- cohorts do not show misleading 0% rows for weeks that simply haven't happened
-- yet.

with signup_cohorts as (
    select
        account_id,
        toStartOfWeek(signup_at) as cohort_week
    from {{ ref('fct_user_activation') }}
),

cohort_size as (
    select cohort_week, count(distinct account_id) as n_accounts
    from signup_cohorts
    group by cohort_week
),

weekly_activity as (
    select
        account_id,
        toStartOfWeek(activity_date) as activity_week
    from {{ ref('int_user_activity') }}
    group by account_id, activity_week
),

-- one row per (cohort account, activity week) joined to its cohort
retained as (
    select
        sc.cohort_week,
        sc.account_id,
        wa.activity_week,
        dateDiff('week', sc.cohort_week, wa.activity_week) as week_offset
    from signup_cohorts sc
    join weekly_activity wa on wa.account_id = sc.account_id
    where wa.activity_week >= sc.cohort_week
),

-- per-cohort maximum observable offset = weeks since the cohort up to the
-- latest activity week in the dataset
cohort_horizon as (
    select
        cs.cohort_week,
        greatest(
            0,
            dateDiff('week', cs.cohort_week, (select max(activity_week) from weekly_activity))
        ) as max_week_offset
    from cohort_size cs
),

-- generate week offsets 0..12, capped per cohort by its observable horizon
offsets as (
    select
        ch.cohort_week,
        o.week_offset
    from cohort_horizon ch
    cross join (select arrayJoin(range(0, 13)) as week_offset) o
    where o.week_offset <= least(12, ch.max_week_offset)
)

select
    cs.cohort_week as cohort_week,
    o.week_offset as week_offset,
    cs.n_accounts as cohort_size,
    count(distinct r.account_id) as retained_accounts,
    count(distinct r.account_id) / nullif(cs.n_accounts, 0) as retention_rate
from cohort_size cs
join offsets o on o.cohort_week = cs.cohort_week
left join retained r
    on r.cohort_week = cs.cohort_week
   and r.week_offset = o.week_offset
group by cs.cohort_week, cs.n_accounts, o.week_offset
