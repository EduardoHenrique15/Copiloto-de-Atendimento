select
    customer_id,
    customer_unique_id,
    lpad(customer_zip_code_prefix, 5, '0') as customer_zip_prefix,
    customer_city,
    upper(customer_state) as customer_state
from {{ source('olist', 'olist_customers_dataset') }}
