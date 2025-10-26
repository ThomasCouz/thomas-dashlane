-- models/intermediate/int_daily_user_events.sql

{{ config(
    materialized = 'incremental',
    transient = false,
    unique_key = ['unique_key'],
    incremental_strategy='merge',
    on_schema_change = 'append_new_columns',
    cluster_by = ['reporting_date'],
) }}

-- the incremental reload is based on the event_date, which is not a system timestamp
-- therefore we can have late arriving data for past dates
-- in order to accommodate that, we choose to reload data for the last 2 days
-- it is recommended to schedule a full refresh of this model from time to time to ensure data integrity
{% set lookback_window_days = 2 %}
{%- set last_day_to_reload_from -%} -- noqa
    (select dateadd(day, -{{ lookback_window_days }}, max(reporting_date)) from {{ this }})
{% endset %} -- noqa


with date_spine as (
    select date_day
    from {{ ref('int_date') }}
    {% if is_incremental() %}
    where date_day >= {{ last_day_to_reload_from }} --noqa
    {% endif %}
),

agg_events as (
    select
        event_at::date as event_date,
        user_id,
        count(*) as cnt_total_events,
        {% for event_name in get_events_list() %}
            -- How many events of this type were performed by the user on that date?
            count(case when event_name = '{{ event_name }}' then 1 end) as cnt_{{ event_name }}_events
            {% if not loop.last %},{% endif %}
        {% endfor %}
    from {{ ref('stg_events') }}
    {% if is_incremental() %} --noqa
    where event_at::date >= {{ last_day_to_reload_from }}
    {% endif %} --noqa
    group by 1, 2
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['ds.date_day', 'u.user_id']) }} as unique_key,
        ds.date_day as reporting_date,
        u.user_id,
        coalesce(ae.cnt_total_events, 0) as cnt_total_events,
        {% for event_name in get_events_list() %}
            coalesce(ae.cnt_{{ event_name }}_events, 0) as cnt_{{ event_name }}_events
            {% if not loop.last %},{% endif %}
        {% endfor %}

    from date_spine as ds
        -- Generate one row per user per day since user creation
        inner join {{ ref('stg_user_attributes') }} as u on ds.date_day >= u.user_created_date
        left join agg_events as ae on ds.date_day = ae.event_date and u.user_id = ae.user_id
)

select *
from final
