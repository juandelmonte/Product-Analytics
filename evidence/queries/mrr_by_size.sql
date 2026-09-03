-- Latest-month MRR by company size (star join).
select
    d.company_size as company_size,
    round(sum(m.mrr), 2) as mrr,
    count(distinct m.account_id) as paying_accounts
from marts.fct_account_mrr m
join marts.dim_accounts d on d.account_id = m.account_id
where m.mrr_month = (select max(mrr_month) from marts.fct_account_mrr)
group by d.company_size
order by mrr desc
