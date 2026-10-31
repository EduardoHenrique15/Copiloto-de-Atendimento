-- Uma avaliação por pedido: a mais recente. É a que define o alvo dos modelos.
select *
from (
    select
        *,
        row_number() over (
            partition by order_id order by review_created_at desc, review_answered_at desc, review_id
        ) as review_rank,
        count(*) over (partition by order_id) as n_reviews
    from {{ ref('stg_reviews') }}
)
where review_rank = 1
