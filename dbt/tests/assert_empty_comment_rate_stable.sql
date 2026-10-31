-- Avisa se a proporção de avaliações sem comentário mudar muito em relação à
-- execução de referência (vars expected_empty_comment_rate e tolerance).
{{ config(severity='warn') }}
with rate as (
    select avg(case when comment_message is null then 1.0 else 0.0 end) as empty_rate
    from {{ ref('stg_reviews') }}
)
select empty_rate, {{ var('expected_empty_comment_rate') }} as expected_rate
from rate
where abs(empty_rate - {{ var('expected_empty_comment_rate') }})
    > {{ var('empty_comment_rate_tolerance') }}
