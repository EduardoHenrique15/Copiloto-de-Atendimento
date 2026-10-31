-- Avaliação deveria ser criada depois da entrega. Na Olist a pesquisa é enviada
-- perto da data estimada, então pedidos atrasados podem ser avaliados antes de
-- chegar. Por isso é só aviso: o número de casos fica registrado no log do dbt
-- e em docs/aprendizado.md.
{{ config(severity='warn') }}
select r.order_id, o.delivered_customer_at, r.review_created_at
from {{ ref('int_order_reviews') }} as r
inner join {{ ref('stg_orders') }} as o using (order_id)
where o.delivered_customer_at is not null
  and cast(r.review_created_at as date) < cast(o.delivered_customer_at as date)
