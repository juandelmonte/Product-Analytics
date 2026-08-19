{% test accepted_range(model, column_name, min_value=none, max_value=none) %}
  {# Generic test: asserts all values in a numeric column fall within [min_value, max_value].
     Example usage in schema.yml:
       columns:
         - name: price
           tests:
             - accepted_range:
                 min_value: 0
  #}
  select *
  from {{ model }}
  where
    {% if min_value is not none %}
      {{ column_name }} < {{ min_value }}
    {% endif %}
    {% if min_value is not none and max_value is not none %} or {% endif %}
    {% if max_value is not none %}
      {{ column_name }} > {{ max_value }}
    {% endif %}
{% endtest %}
