-- dim_features.sql
-- Grain: one row per feature code.
--
-- Feature dimension: canonical feature codes and their human-readable labels,
-- derived from the event → feature mapping in the event catalogue.

select
    feature_code,
    case
        when feature_code = 'workspace'     then 'Workspace'
        when feature_code = 'projects'      then 'Projects'
        when feature_code = 'tasks'         then 'Tasks'
        when feature_code = 'comments'      then 'Comments'
        when feature_code = 'integrations'  then 'Integrations'
        else feature_code
    end as feature_name
from (
    select 'workspace'    as feature_code
    union all select 'projects'
    union all select 'tasks'
    union all select 'comments'
    union all select 'integrations'
)
