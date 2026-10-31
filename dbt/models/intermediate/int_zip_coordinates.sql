-- Coordenada média por prefixo de CEP. Descarta pontos fora do território
-- brasileiro, que existem na base original e distorceriam a média.
select
    zip_prefix,
    avg(lat) as lat,
    avg(lng) as lng,
    count(*) as n_points
from {{ ref('stg_geolocation') }}
where lat between -34.0 and 5.5
  and lng between -74.0 and -34.0
group by zip_prefix
