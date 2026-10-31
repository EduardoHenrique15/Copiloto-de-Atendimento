-- Uma linha por pedido entregue e avaliado, para estimar o efeito do atraso
-- (tratamento is_late) na nota. Confundidores: o que influencia ao mesmo tempo
-- o atraso e a nota, todos conhecidos antes do envio.
select
    o.order_id,
    o.purchased_at,
    date_trunc('month', o.purchased_at) as purchase_month,

    -- Tratamento
    o.is_late,
    o.delay_days,

    -- Resultado
    r.review_score,
    r.review_score <= 2 as is_negative,

    -- Confundidores
    o.promised_days,
    o.distance_km,
    o.same_state,
    o.customer_state,
    o.seller_state,
    o.main_category,
    o.n_items,
    o.n_sellers,
    o.items_price,
    o.freight_value,
    o.freight_ratio,
    o.main_payment_type,
    o.max_installments,
    h.seller_prior_orders,
    h.seller_prior_avg_score,
    h.seller_prior_late_rate
from {{ ref('int_orders_enriched') }} as o
inner join {{ ref('int_order_reviews') }} as r using (order_id)
left join {{ ref('int_seller_history_asof') }} as h using (order_id)
where o.order_status = 'delivered'
  and o.delivered_customer_at is not null
