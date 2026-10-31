# Resumo da análise exploratória

Gerado por `scripts/eda_resumo.py` a partir dos marts do dbt. Não edite à mão.

| Métrica | Valor |
| --- | ---: |
| Pedidos na base | 99,441 |
| Pedidos entregues (status delivered, com data de entrega) | 96,470 |
| Primeira compra | 2016-09-04 |
| Última compra | 2018-10-17 |
| Avaliações (linhas) | 99,224 |
| Pedidos com mais de uma avaliação | 547 |
| Avaliações com comentário preenchido | 40,968 |
| Proporção de avaliações sem comentário | 0.5871 |
| Linhas em fct_orders_risk (entregues e avaliados) | 95,824 |
| Taxa de avaliação negativa (nota 1 ou 2) | 0.1281 |
| Taxa de pedidos atrasados | 0.0799 |
| Taxa negativa entre atrasados | 0.5405 |
| Taxa negativa entre entregues no prazo | 0.0922 |
| Nota média dos atrasados | 2.5653 |
| Nota média dos entregues no prazo | 4.2940 |
| Reclamações com texto (nota até 3) em fct_complaints | 14,447 |
| Linhas em fct_orders_causal | 95,824 |
| Pedidos sem distância (CEP sem coordenada) | 476 |
| Avaliações criadas antes da entrega (dia) | 4,967 |
| Pedidos com entrega antes da compra | 0 |

## Distribuição das notas (uma avaliação por pedido)

| Nota | Pedidos | Proporção |
| ---: | ---: | ---: |
| 1 | 11,366 | 0.1152 |
| 2 | 3,129 | 0.0317 |
| 3 | 8,133 | 0.0824 |
| 4 | 19,044 | 0.1930 |
| 5 | 57,001 | 0.5777 |

## Taxa de nota negativa por atraso (fct_orders_risk)

| Faixa | Pedidos | Taxa negativa |
| --- | ---: | ---: |
| 1. 10+ dias adiantado | 56,905 | 0.0895 |
| 2. até 10 dias adiantado | 31,258 | 0.0971 |
| 3. 1 a 3 dias de atraso | 2,636 | 0.1912 |
| 4. 4 a 10 dias de atraso | 2,793 | 0.6688 |
| 5. mais de 10 dias de atraso | 2,232 | 0.7926 |

A diferença entre atrasados e no prazo é correlação, não efeito causal.
O efeito do atraso é estimado na Fase 3, controlando confundidores.
