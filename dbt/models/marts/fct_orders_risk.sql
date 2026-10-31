-- Uma linha por pedido entregue e avaliado. Features só com o que se sabe até
-- a entrega (feature_cutoff_at); o alvo vem da avaliação, que é posterior.
-- As colunas de avaliação (review_*) são ALVO, nunca feature.
select
    o.order_id,
    o.purchased_at,
    o.delivered_customer_at as feature_cutoff_at,
    o.estimated_delivery_at,

    -- Features de entrega
    o.promised_days,
    o.delivery_days,
    o.delay_days,
    o.is_late,

    -- Features do pedido
    o.n_items,
    o.n_products,
    o.n_sellers,
    o.items_price,
    o.freight_value,
    o.freight_ratio,
    o.main_category,
    o.main_payment_type,
    o.max_installments,
    o.n_payment_types,

    -- Features geográficas
    o.customer_state,
    o.seller_state,
    o.same_state,
    o.distance_km,

    -- Histórico do vendedor (as-of compra)
    o.main_seller_id as seller_id,
    h.seller_prior_orders,
    h.seller_prior_avg_score,
    h.seller_prior_n_reviews,
    h.seller_prior_late_rate,
    h.seller_prior_n_delivered,

    -- Alvo
    r.review_created_at,
    r.review_score,
    r.review_score <= 2 as is_negative
from {{ ref('int_orders_enriched') }} as o
inner join {{ ref('int_order_reviews') }} as r using (order_id)
left join {{ ref('int_seller_history_asof') }} as h using (order_id)
where o.order_status = 'delivered'
  and o.delivered_customer_at is not null
