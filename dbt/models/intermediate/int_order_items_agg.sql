-- Resumo dos itens por pedido. O vendedor e a categoria "principais" são os do
-- item mais caro (empate: menor order_item_id).
with items as (
    select
        i.*,
        coalesce(t.category_name_en, p.category_name, 'unknown') as category,
        row_number() over (
            partition by i.order_id order by i.price desc, i.order_item_id
        ) as price_rank
    from {{ ref('stg_order_items') }} as i
    left join {{ ref('stg_products') }} as p using (product_id)
    left join {{ ref('stg_category_translation') }} as t on t.category_name = p.category_name
)

select
    order_id,
    count(*) as n_items,
    count(distinct product_id) as n_products,
    count(distinct seller_id) as n_sellers,
    sum(price) as items_price,
    sum(freight_value) as freight_value,
    max(case when price_rank = 1 then seller_id end) as main_seller_id,
    max(case when price_rank = 1 then category end) as main_category,
    max(shipping_limit_at) as shipping_limit_at
from items
group by order_id
