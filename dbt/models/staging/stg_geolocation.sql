select
    lpad(geolocation_zip_code_prefix, 5, '0') as zip_prefix,
    cast(geolocation_lat as double) as lat,
    cast(geolocation_lng as double) as lng,
    geolocation_city as city,
    upper(geolocation_state) as state
from {{ source('olist', 'olist_geolocation_dataset') }}
