{% macro year_of(column_name) %}
  {% if target.type == 'clickhouse' %}
    toYear({{ column_name }})
  {% else %}
    date_part('year', {{ column_name }})
  {% endif %}
{% endmacro %}

{% macro month_of(column_name) %}
  {% if target.type == 'clickhouse' %}
    toMonth({{ column_name }})
  {% else %}
    date_part('month', {{ column_name }})
  {% endif %}
{% endmacro %}

{% macro trunc_to_month(column_name) %}
  date_trunc('month', {{ column_name }})
{% endmacro %}
