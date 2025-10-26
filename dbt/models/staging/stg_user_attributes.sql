-- models/staging/stg_user_attributes.sql

with final as (
    select
        user_id,
        user_created_on::date as user_created_date,
        creation_app_platform,
        case
            when creation_app_platform = 'ios' then 'App Store'
            when creation_app_platform = 'android' then 'Google Play'
            when creation_app_platform in ('web', 'saex', 'catalyst') then 'Desktop'
        end as creation_app_source,
        user_retained_4_weeks::boolean as is_retained_4_weeks
    from {{ source('csv_files', 'user_attributes') }}
    -- 5 users have a value of -3 for user_retained_4_weeks: needs investigation
    where is_retained_4_weeks in (0, 1)
)

select *
from final
