{% macro get_events_list() %}

{% set events_list = [ 'log_in_to_dashlane', 'add_new_password_to_vault',  'add_new_personal_document_to_vault',
                        'add_new_payment_method_to_vault',  'perform_autofill', 'generate_password'] %}
{{ return(events_list) }}

{% endmacro %}
