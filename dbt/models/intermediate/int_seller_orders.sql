-- Uma linha por (vendedor, pedido) com as datas e resultados de cada pedido.
-- Base para o histórico "as-of" do vendedor.
select distinct
    i.seller_id,
    o.order_id,
    o.purchased_at,
    o.delivered_customer_at,
    o.estimated_delivery_at,
    r.review_created_at,
    r.review_score
from {{ ref('stg_order_items') }} as i
inner join {{ ref('stg_orders') }} as o using (order_id)
left join {{ ref('int_order_reviews') }} as r using (order_id)
