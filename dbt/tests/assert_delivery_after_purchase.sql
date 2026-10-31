-- Entrega ao cliente não pode ser antes da compra.
-- A base real pode ter poucos registros inconsistentes: avisa a partir de 1
-- e só falha se passar de 100 (proporção irrelevante em ~100 mil pedidos).
{{ config(severity='error', warn_if='>0', error_if='>100') }}
select order_id, purchased_at, delivered_customer_at
from {{ ref('stg_orders') }}
where delivered_customer_at < purchased_at
