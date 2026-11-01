# Triagem: comparação no ouro (test)

Gerado por `scripts/evaluate_triage.py`. Não edite à mão.

`problema_entrega` junta `atraso_entrega` e `nao_recebido` (ADR 0007, emenda 2): o status do pedido separa os dois no serviço.

| Abordagem | F1 macro | Acurácia | p50 | p95 | R$ / 1.000 tickets |
| --- | ---: | ---: | ---: | ---: | ---: |
| embeddings_lr | 0.639 | 71.5% | 26 ms | 37 ms | R$ 0.00 |
| zero_shot | 0.738 | 83.5% | 1023 ms | 5039 ms | R$ 1.64 |

## embeddings_lr

Base do custo: tempo de CPU x preço-hora da máquina. Roteamento: com confiança mínima 0.75 (escolhida na validação), 47% dos tickets são classificados automaticamente, com acurácia de 86.2% (meta 85%); o resto vai para revisão humana.

| Categoria | Precisão | Recall | F1 | Suporte |
| --- | ---: | ---: | ---: | ---: |
| problema_entrega | 0.86 | 0.74 | 0.80 | 66 |
| produto_errado_ou_incompleto | 0.84 | 0.74 | 0.79 | 43 |
| produto_defeituoso_ou_qualidade | 0.74 | 0.70 | 0.72 | 33 |
| diferente_do_anuncio | 0.61 | 0.65 | 0.63 | 17 |
| atendimento_vendedor | 0.67 | 0.67 | 0.67 | 6 |
| cancelamento_ou_cobranca | 0.52 | 0.75 | 0.62 | 16 |
| outro | 0.09 | 0.14 | 0.11 | 7 |
| sem_problema | 0.69 | 0.92 | 0.79 | 12 |

| Fatia | n | Acurácia |
| --- | ---: | ---: |
| curtos (<= 30 caracteres) | 26 | 76.9% |
| longos (> 300 caracteres) | 0 | n/d |
| mais de um problema | 60 | 53.3% |
| um problema só | 140 | 79.3% |

Matriz de confusão (linhas: humano; colunas: previsto):

| | problema_ent | produto_erra | produto_defe | diferente_do | atendimento_ | cancelamento | outro | sem_problema |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| problema_ent | 49 | 5 | 3 | 0 | 1 | 4 | 3 | 1 |
| produto_erra | 3 | 32 | 3 | 2 | 0 | 1 | 2 | 0 |
| produto_defe | 1 | 0 | 23 | 2 | 0 | 2 | 3 | 2 |
| diferente_do | 0 | 0 | 1 | 11 | 1 | 2 | 1 | 1 |
| atendimento_ | 0 | 0 | 0 | 0 | 4 | 2 | 0 | 0 |
| cancelamento | 2 | 1 | 0 | 0 | 0 | 12 | 1 | 0 |
| outro | 1 | 0 | 1 | 3 | 0 | 0 | 1 | 1 |
| sem_problema | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 11 |

## zero_shot

Base do custo: tokens x preço do LLM. Roteamento: com confiança mínima 0.95 (escolhida na validação), 75% dos tickets são classificados automaticamente, com acurácia de 92.0% (meta 85%); o resto vai para revisão humana.

| Categoria | Precisão | Recall | F1 | Suporte |
| --- | ---: | ---: | ---: | ---: |
| problema_entrega | 0.95 | 0.86 | 0.90 | 66 |
| produto_errado_ou_incompleto | 0.88 | 0.98 | 0.92 | 43 |
| produto_defeituoso_ou_qualidade | 0.84 | 0.79 | 0.81 | 33 |
| diferente_do_anuncio | 0.76 | 0.76 | 0.76 | 17 |
| atendimento_vendedor | 1.00 | 0.33 | 0.50 | 6 |
| cancelamento_ou_cobranca | 0.58 | 0.88 | 0.70 | 16 |
| outro | 0.43 | 0.43 | 0.43 | 7 |
| sem_problema | 0.91 | 0.83 | 0.87 | 12 |

| Fatia | n | Acurácia |
| --- | ---: | ---: |
| curtos (<= 30 caracteres) | 26 | 80.8% |
| longos (> 300 caracteres) | 0 | n/d |
| mais de um problema | 60 | 66.7% |
| um problema só | 140 | 90.7% |

Matriz de confusão (linhas: humano; colunas: previsto):

| | problema_ent | produto_erra | produto_defe | diferente_do | atendimento_ | cancelamento | outro | sem_problema |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| problema_ent | 57 | 1 | 3 | 1 | 0 | 4 | 0 | 0 |
| produto_erra | 0 | 42 | 0 | 0 | 0 | 1 | 0 | 0 |
| produto_defe | 0 | 1 | 26 | 3 | 0 | 1 | 2 | 0 |
| diferente_do | 0 | 3 | 0 | 13 | 0 | 1 | 0 | 0 |
| atendimento_ | 0 | 0 | 1 | 0 | 2 | 3 | 0 | 0 |
| cancelamento | 1 | 0 | 0 | 0 | 0 | 14 | 1 | 0 |
| outro | 2 | 1 | 0 | 0 | 0 | 0 | 3 | 1 |
| sem_problema | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 10 |
