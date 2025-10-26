{% snapshot snapshot_user_attributes %}

{{ config(
    target_schema = 'snapshots',
    unique_key = 'user_id',
    strategy = 'check',
    check_cols = ['user_retained_4_weeks'],
)
}}

    select
        user_id,
        user_retained_4_weeks
    from {{ source('csv_files', 'user_attributes') }}

{% endsnapshot %}
