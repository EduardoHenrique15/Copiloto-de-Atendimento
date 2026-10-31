-- Resumo dos pagamentos por pedido. A forma "principal" é a de maior valor.
with ranked as (
    select
        *,
        row_number() over (
            partition by order_id order by payment_value desc, payment_sequential
        ) as value_rank
    from {{ ref('stg_payments') }}
)

select
    order_id,
    sum(payment_value) as payment_value,
    count(distinct payment_type) as n_payment_types,
    max(payment_installments) as max_installments,
    max(case when value_rank = 1 then payment_type end) as main_payment_type
from ranked
group by order_id
