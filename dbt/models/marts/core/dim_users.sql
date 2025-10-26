-- models/marts/analytics/dim_users.sql

{{ config(
    materialized = 'view',
) }}

with final as (
    select
        user_id,
        user_created_date,
        creation_app_platform,
        creation_app_source,
        is_retained_4_weeks
    from {{ ref('stg_user_attributes') }}
)

select *
from final
