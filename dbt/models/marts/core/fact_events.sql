-- models/marts/analytics/fact_events.sql

{{ config(
    materialized = 'view',
) }}

with final as (
select event_id,
       event_name,
       user_id,
       event_at
from {{ ref('stg_events') }}
)

select *
from final
