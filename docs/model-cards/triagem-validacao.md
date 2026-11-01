# Triagem: comparação no ouro (val)

Gerado por `scripts/evaluate_triage.py`. Não edite à mão.

| Abordagem | F1 macro | Acurácia | p50 | p95 | R$ / 1.000 tickets |
| --- | ---: | ---: | ---: | ---: | ---: |
| embeddings_lr | 0.560 | 65.0% | 28 ms | 41 ms | R$ 0.00 |
| zero_shot | 0.532 | 72.0% | 1022 ms | 1663 ms | R$ 1.64 |

## embeddings_lr

Base do custo: tempo de CPU x preço-hora da máquina. Roteamento: com confiança mínima 0.75, 36% dos tickets são classificados automaticamente, com acurácia de 86.1% (meta 85%); o resto vai para revisão humana.

| Categoria | Precisão | Recall | F1 | Suporte |
| --- | ---: | ---: | ---: | ---: |
| atraso_entrega | 0.91 | 0.53 | 0.67 | 19 |
| nao_recebido | 0.58 | 0.58 | 0.58 | 12 |
| produto_errado_ou_incompleto | 0.77 | 0.71 | 0.74 | 28 |
| produto_defeituoso_ou_qualidade | 0.86 | 0.63 | 0.73 | 19 |
| diferente_do_anuncio | 0.38 | 1.00 | 0.55 | 3 |
| atendimento_vendedor | 0.00 | 0.00 | 0.00 | 2 |
| cancelamento_ou_cobranca | 0.29 | 0.67 | 0.40 | 6 |
| outro | 0.40 | 0.50 | 0.44 | 4 |
| sem_problema | 0.88 | 1.00 | 0.93 | 7 |

| Fatia | n | Acurácia |
| --- | ---: | ---: |
| curtos (<= 30 caracteres) | 16 | 81.2% |
| longos (> 300 caracteres) | 0 | n/d |
| mais de um problema | 32 | 53.1% |
| um problema só | 68 | 70.6% |

Matriz de confusão (linhas: humano; colunas: previsto):

| | atraso_entre | nao_recebido | produto_erra | produto_defe | diferente_do | atendimento_ | cancelamento | outro | sem_problema |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| atraso_entre | 10 | 1 | 2 | 0 | 0 | 1 | 4 | 1 | 0 |
| nao_recebido | 1 | 7 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| produto_erra | 0 | 2 | 20 | 2 | 2 | 0 | 2 | 0 | 0 |
| produto_defe | 0 | 1 | 3 | 12 | 2 | 0 | 0 | 1 | 0 |
| diferente_do | 0 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| atendimento_ | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| cancelamento | 0 | 0 | 0 | 0 | 0 | 1 | 4 | 1 | 0 |
| outro | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 2 | 0 |
| sem_problema | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |

## zero_shot

Base do custo: tokens x preço do LLM. Roteamento: com confiança mínima 0.95, 79% dos tickets são classificados automaticamente, com acurácia de 78.5% (meta 85%); o resto vai para revisão humana.

| Categoria | Precisão | Recall | F1 | Suporte |
| --- | ---: | ---: | ---: | ---: |
| atraso_entrega | 0.80 | 0.42 | 0.55 | 19 |
| nao_recebido | 0.56 | 0.75 | 0.64 | 12 |
| produto_errado_ou_incompleto | 0.87 | 0.93 | 0.90 | 28 |
| produto_defeituoso_ou_qualidade | 1.00 | 0.89 | 0.94 | 19 |
| diferente_do_anuncio | 0.17 | 0.33 | 0.22 | 3 |
| atendimento_vendedor | 0.00 | 0.00 | 0.00 | 2 |
| cancelamento_ou_cobranca | 0.44 | 0.67 | 0.53 | 6 |
| outro | 0.00 | 0.00 | 0.00 | 4 |
| sem_problema | 1.00 | 1.00 | 1.00 | 7 |

| Fatia | n | Acurácia |
| --- | ---: | ---: |
| curtos (<= 30 caracteres) | 16 | 87.5% |
| longos (> 300 caracteres) | 0 | n/d |
| mais de um problema | 32 | 62.5% |
| um problema só | 68 | 76.5% |

Matriz de confusão (linhas: humano; colunas: previsto):

| | atraso_entre | nao_recebido | produto_erra | produto_defe | diferente_do | atendimento_ | cancelamento | outro | sem_problema |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| atraso_entre | 8 | 6 | 2 | 0 | 1 | 0 | 2 | 0 | 0 |
| nao_recebido | 0 | 9 | 0 | 0 | 0 | 0 | 3 | 0 | 0 |
| produto_erra | 0 | 1 | 26 | 0 | 1 | 0 | 0 | 0 | 0 |
| produto_defe | 0 | 0 | 0 | 17 | 2 | 0 | 0 | 0 | 0 |
| diferente_do | 0 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 |
| atendimento_ | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| cancelamento | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 2 | 0 |
| outro | 1 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 |
| sem_problema | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
