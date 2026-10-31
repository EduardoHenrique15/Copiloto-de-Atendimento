-- Uma linha por comentário de avaliação com nota até 3. Base da triagem e do
-- copiloto. Inclui o contexto do pedido, sem dados pessoais.
select
    md5(r.review_id || '|' || r.order_id) as complaint_id,
    r.review_id,
    r.order_id,
    r.review_score,
    r.comment_title,
    r.comment_message,
    length(r.comment_message) as comment_length,
    r.review_created_at,
    o.order_status,
    o.purchased_at,
    o.delivered_customer_at,
    o.estimated_delivery_at,
    o.delay_days,
    o.is_late,
    o.main_category,
    o.n_items,
    o.items_price,
    o.freight_value
from {{ ref('stg_reviews') }} as r
left join {{ ref('int_orders_enriched') }} as o using (order_id)
where r.review_score <= 3
  and r.comment_message is not null
