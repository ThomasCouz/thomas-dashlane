/*
This macro is utilized to create the schema output for our dbt models.
In some cases, we leverage the default schema to concatenate with the schema we specify.
For the cases below, we have altered this to EXCLUDE the default dbt_ prefix:
    1) files that start with the stg_ prefix
    2) files that start with the base_gainsight prefix
    3) files in the transformation/intermediate directory
*/

{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}

    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}

{%- endmacro %}
