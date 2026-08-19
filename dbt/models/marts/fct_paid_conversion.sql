-- fct_paid_conversion.sql
-- Grain: one row per account.
--
-- Paid conversion: has the account ever had a paid (pro/enterprise) subscription?

with paid as (
    select distinct account_id
    from {{ ref('int_subscription_history') }}
    where plan_code in ('pro', 'enterprise')
)

select
    a.account_id,
    case when p.account_id is not null then true else false end as is_converted
from {{ ref('int_identity_mapping') }} a
left join paid p on p.account_id = a.account_id
