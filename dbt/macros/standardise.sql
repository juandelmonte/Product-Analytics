{% macro standardise_country(column_name) %}
  {# Map messy country variants (US/USA/United States, CA/Canada/CAN, ...) to ISO2. #}
  case
    when lower(toString({{ column_name }})) in ('us', 'usa', 'united states', 'united states of america') then 'US'
    when lower(toString({{ column_name }})) in ('ca', 'can', 'canada') then 'CA'
    when lower(toString({{ column_name }})) in ('gb', 'uk', 'united kingdom') then 'GB'
    else toString({{ column_name }})
  end
{% endmacro %}

{% macro standardise_plan(column_name) %}
  {# Map messy plan names (Pro/pro/PRO, Enterprise/enterprise/ENT, ...) to codes. #}
  case
    when lower(toString({{ column_name }})) in ('free') then 'free'
    when lower(toString({{ column_name }})) in ('trial') then 'trial'
    when lower(toString({{ column_name }})) in ('pro') then 'pro'
    when lower(toString({{ column_name }})) in ('enterprise', 'ent') then 'enterprise'
    else lower(toString({{ column_name }}))
  end
{% endmacro %}

{% macro standardise_frequency(column_name) %}
  {# Map messy billing frequencies (Monthly/month, Annual/year) to canonical. #}
  case
    when lower(toString({{ column_name }})) in ('monthly', 'month') then 'monthly'
    when lower(toString({{ column_name }})) in ('annual', 'year') then 'annual'
    else lower(toString({{ column_name }}))
  end
{% endmacro %}
