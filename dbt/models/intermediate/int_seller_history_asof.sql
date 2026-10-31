-- Histórico do vendedor principal de cada pedido, calculado só com o que já se
-- sabia no momento da compra (as-of purchased_at):
--   * volume: pedidos do vendedor comprados antes;
--   * nota média: avaliações criadas antes;
--   * taxa de atraso: pedidos entregues antes.
-- Nenhuma informação posterior à compra entra aqui. Isso é verificado em testes.
with current_orders as (
    select o.order_id, o.purchased_at, a.main_seller_id as seller_id
    from {{ ref('stg_orders') }} as o
    inner join {{ ref('int_order_items_agg') }} as a using (order_id)
)

select
    c.order_id,
    c.seller_id,
    count(p.order_id) as seller_prior_orders,
    avg(case when p.review_created_at < c.purchased_at then p.review_score end)
        as seller_prior_avg_score,
    count(case when p.review_created_at < c.purchased_at then 1 end)
        as seller_prior_n_reviews,
    avg(
        case
            when p.delivered_customer_at < c.purchased_at
                then cast(p.delivered_customer_at > p.estimated_delivery_at as integer)
        end
    ) as seller_prior_late_rate,
    count(case when p.delivered_customer_at < c.purchased_at then 1 end)
        as seller_prior_n_delivered
from current_orders as c
left join {{ ref('int_seller_orders') }} as p
    on p.seller_id = c.seller_id
    and p.purchased_at < c.purchased_at
    and p.order_id <> c.order_id
group by c.order_id, c.seller_id
