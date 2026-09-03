-- Average feature adoption rate per feature.
select
    feature_code,
    round(avg(adoption_rate), 4) as avg_adoption_rate,
    sum(accounts_using_feature)  as accounts_using_feature
from marts.fct_feature_adoption
group by feature_code
order by avg_adoption_rate desc
