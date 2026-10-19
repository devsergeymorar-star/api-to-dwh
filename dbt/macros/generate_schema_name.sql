{#- Use the configured schema (ClickHouse database) as-is instead of "<target>_<schema>". -#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name is not none else target.schema }}
{%- endmacro %}
