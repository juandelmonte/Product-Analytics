-- Feature adoption rate over time (weekly), per feature.
select
    week,
    feature_code,
    adoption_rate
from marts.fct_feature_adoption
order by week, feature_code
