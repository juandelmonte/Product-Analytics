-- High-level KPIs for the overview page.
select
    (select countDistinct(account_id) from marts.fct_user_activation)          as total_accounts,
    (select countIf(is_activated) from marts.fct_user_activation)              as activated_accounts,
    (select round(countIf(is_activated) / count(), 4) from marts.fct_user_activation) as activation_rate,
    (select countIf(is_converted) from marts.fct_paid_conversion)              as converted_accounts,
    (select round(countIf(is_converted) / count(), 4) from marts.fct_paid_conversion) as paid_conversion_rate,
    (select round(sum(mrr), 2) from marts.fct_account_mrr
        where mrr_month = (select max(mrr_month) from marts.fct_account_mrr))  as latest_month_mrr,
    (select count() from marts.fct_product_events)                             as total_events,
    (select round(avg(adoption_rate), 4) from marts.fct_feature_adoption)      as avg_feature_adoption
