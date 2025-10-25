-- models/marts/analytics/fact_daily_user_events.sql

{{ config(
    materialized = 'view',
) }}

with final as (
select unique_key,
       reporting_date,
       user_id,
       cnt_total_events,
       cnt_log_in_to_dashlane_events,
       cnt_add_new_password_to_vault_events,
       cnt_add_new_personal_document_to_vault_events,
       cnt_add_new_payment_method_to_vault_events,
       cnt_perform_autofill_events,
       cnt_generate_password_events
from {{ ref('int_daily_user_events') }}
)

select *
from final
