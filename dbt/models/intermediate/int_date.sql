{{ config(
    materialized = 'view',
) }}

with final as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="'" ~ var('default_start_date') ~ "'::date",
        end_date="'" ~ var('default_end_date') ~ "'::date",
        )
    }}
)

select *
from final
