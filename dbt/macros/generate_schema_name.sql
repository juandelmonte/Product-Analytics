{% macro generate_schema_name(custom_schema_name, node) -%}
  {# Use flat schema names (no target-schema prefix).
     In ClickHouse `schema` is the database, so this keeps databases clean:
       seeds   -> raw
       staging -> staging
       marts   -> marts
     (The default behaviour would prefix with the profile schema, e.g. `analytics_raw`.)
  #}
  {%- if custom_schema_name is none -%}
    {{ target.schema }}
  {%- else -%}
    {{ custom_schema_name | trim }}
  {%- endif -%}
{%- endmacro %}
