{# Por defecto dbt crea esquemas como "main_marts". Así se llaman simplemente "marts". #}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}
