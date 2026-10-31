select
    seller_id,
    lpad(seller_zip_code_prefix, 5, '0') as seller_zip_prefix,
    seller_city,
    upper(seller_state) as seller_state
from {{ source('olist', 'olist_sellers_dataset') }}
