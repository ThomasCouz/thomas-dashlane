-- models/staging/stg_events.sql

with final as (
    select
        event_id,
        event_name,
        user_id,
        event_at::timestamptz as event_at
    from {{ source('csv_files', 'events') }}
)

select *
from final
