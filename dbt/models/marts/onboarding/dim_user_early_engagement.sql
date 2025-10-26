-- models/marts/onboarding/dim_user_early_engagement.sql

select
    u.user_id,
    u.is_retained_4_weeks,
    u.creation_app_platform,
    fu.* exclude user_id
from {{ ref('int_users_f7d_features_usage') }} as fu
    inner join {{ ref('stg_user_attributes') }} as u on fu.user_id = u.user_id
