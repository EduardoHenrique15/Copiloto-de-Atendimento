{#- Diferença em dias (com fração) entre dois timestamps: end - start. -#}
{% macro days_between(start_ts, end_ts) -%}
    (epoch({{ end_ts }}) - epoch({{ start_ts }})) / 86400.0
{%- endmacro %}
