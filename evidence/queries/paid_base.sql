-- Daily evolution of the paid base.
select
    day_date,
    cum_converted,
    cum_churned,
    paid_accounts
from marts.fct_paid_base_daily
order by day_date
