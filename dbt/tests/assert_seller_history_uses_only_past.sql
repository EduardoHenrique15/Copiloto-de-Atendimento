-- Anti-vazamento: o histórico do vendedor de cada pedido precisa ser
-- reproduzível usando apenas pedidos comprados antes dele. Recalcula o volume
-- de forma independente e falha se divergir.
with recomputed as (
    select c.order_id, count(distinct p.order_id) as n_prior
    from {{ ref('fct_orders_risk') }} as c
    left join {{ ref('int_seller_orders') }} as p
        on p.seller_id = c.seller_id
        and p.purchased_at < c.purchased_at
    group by c.order_id
)
select f.order_id, f.seller_prior_orders, r.n_prior
from {{ ref('fct_orders_risk') }} as f
inner join recomputed as r using (order_id)
where f.seller_prior_orders <> r.n_prior
