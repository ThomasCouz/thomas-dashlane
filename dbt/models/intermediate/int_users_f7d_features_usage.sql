-- models/marts/analytics/int_users_f7d_features_usage.sql

with features_usage_7d as (
    select
        *,
        {% for event_name in get_events_list() %}
            cnt_{{ event_name }}_events > 0 as has_{{ event_name }}
            {% if not loop.last %},{% endif %}
        {% endfor %},
        row_number() over (partition by user_id order by reporting_date) as days_since_user_created
    from {{ ref('int_daily_user_events') }}
    qualify days_since_user_created <= 7
),

final as (
    select
        user_id,
        {% for event_name in get_events_list() %}
            -- Has the user performed the event in the first 7 days after user creation?
            boolor_agg(has_{{ event_name }}) as has_{{ event_name }}_f7d,
            -- On how many distinct days has the user performed the event in the first 7 days after user creation?
            count(distinct case when has_{{ event_name }} then reporting_date end) as cnt_days_{{ event_name }}_f7d,
            -- How many times has the used performed the event in the first 7 days after user creation?
            sum(cnt_{{ event_name }}_events) as cnt_{{ event_name }}_events_f7d
            {% if not loop.last %},{% endif %}
        {% endfor %}
    from features_usage_7d
    group by 1
)

select *
from final
