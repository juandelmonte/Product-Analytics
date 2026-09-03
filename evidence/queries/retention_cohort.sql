-- Weekly cohort retention (cohort_week x week_offset).
select
    cohort_week,
    week_offset,
    cohort_size,
    retained_accounts,
    round(retention_rate, 4) as retention_rate
from marts.fct_retention
order by cohort_week, week_offset
