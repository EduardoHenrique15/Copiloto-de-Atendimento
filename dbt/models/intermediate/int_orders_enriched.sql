-- Pedido com cliente, itens, pagamentos, vendedor principal, distância e
-- métricas de entrega. Ainda sem filtro de status.
select
    o.order_id,
    o.customer_id,
    o.order_status,
    o.purchased_at,
    o.approved_at,
    o.delivered_carrier_at,
    o.delivered_customer_at,
    o.estimated_delivery_at,
    c.customer_state,
    s.seller_state,
    c.customer_state = s.seller_state as same_state,
    {{ haversine_km('cg.lat', 'cg.lng', 'sg.lat', 'sg.lng') }} as distance_km,
    i.n_items,
    i.n_products,
    i.n_sellers,
    i.items_price,
    i.freight_value,
    i.freight_value / nullif(i.items_price, 0) as freight_ratio,
    i.main_seller_id,
    i.main_category,
    p.payment_value,
    p.main_payment_type,
    p.max_installments,
    p.n_payment_types,
    {{ days_between('o.purchased_at', 'o.estimated_delivery_at') }} as promised_days,
    {{ days_between('o.purchased_at', 'o.delivered_customer_at') }} as delivery_days,
    -- Positivo = atraso; negativo = entregou antes do prazo estimado.
    {{ days_between('o.estimated_delivery_at', 'o.delivered_customer_at') }} as delay_days,
    case
        when o.delivered_customer_at is null then null
        else o.delivered_customer_at > o.estimated_delivery_at
    end as is_late
from {{ ref('stg_orders') }} as o
left join {{ ref('stg_customers') }} as c using (customer_id)
left join {{ ref('int_order_items_agg') }} as i using (order_id)
left join {{ ref('int_order_payments_agg') }} as p using (order_id)
left join {{ ref('stg_sellers') }} as s on s.seller_id = i.main_seller_id
left join {{ ref('int_zip_coordinates') }} as cg on cg.zip_prefix = c.customer_zip_prefix
left join {{ ref('int_zip_coordinates') }} as sg on sg.zip_prefix = s.seller_zip_prefix
