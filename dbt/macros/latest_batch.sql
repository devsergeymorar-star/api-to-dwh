{#-
  Raw tables are append-only: a re-run or backfill adds another batch for the same day.
  Keep the most recent payload per (_partition_date, _record_key).
-#}
{% macro latest_batch(relation) -%}
    select
        _partition_date,
        _record_key,
        argMax(payload, _loaded_at) as payload,
        max(_loaded_at) as loaded_at
    from {{ relation }}
    group by _partition_date, _record_key
{%- endmacro %}
