-- Uma linha por (review_id, order_id). Na base real, o mesmo review_id pode
-- aparecer em mais de um pedido, e um pedido pode ter mais de uma avaliação.
select
    review_id,
    order_id,
    cast(review_score as integer) as review_score,
    nullif(trim(review_comment_title), '') as comment_title,
    nullif(trim(review_comment_message), '') as comment_message,
    cast(review_creation_date as timestamp) as review_created_at,
    cast(review_answer_timestamp as timestamp) as review_answered_at
from {{ source('olist', 'olist_order_reviews_dataset') }}
