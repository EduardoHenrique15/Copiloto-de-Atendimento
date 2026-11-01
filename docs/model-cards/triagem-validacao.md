# Triagem: comparação no ouro (val)

Gerado por `scripts/evaluate_triage.py`. Não edite à mão.

`problema_entrega` junta `atraso_entrega` e `nao_recebido` (ADR 0007, emenda 2): o status do pedido separa os dois no serviço.

| Abordagem | F1 macro | Acurácia | p50 | p95 | R$ / 1.000 tickets |
| --- | ---: | ---: | ---: | ---: | ---: |
| embeddings_lr | 0.562 | 67.0% | 28 ms | 41 ms | R$ 0.00 |
| zero_shot | 0.568 | 78.0% | 996 ms | 1795 ms | R$ 1.64 |

## embeddings_lr

Base do custo: tempo de CPU x preço-hora da máquina. Roteamento: com confiança mínima 0.75, 36% dos tickets são classificados automaticamente, com acurácia de 86.1% (meta 85%); o resto vai para revisão humana.

| Categoria | Precisão | Recall | F1 | Suporte |
| --- | ---: | ---: | ---: | ---: |
| problema_entrega | 0.83 | 0.61 | 0.70 | 31 |
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
| um problema só | 68 | 73.5% |

Matriz de confusão (linhas: humano; colunas: previsto):

| | problema_ent | produto_erra | produto_defe | diferente_do | atendimento_ | cancelamento | outro | sem_problema |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| problema_ent | 19 | 2 | 0 | 0 | 1 | 8 | 1 | 0 |
| produto_erra | 2 | 20 | 2 | 2 | 0 | 2 | 0 | 0 |
| produto_defe | 1 | 3 | 12 | 2 | 0 | 0 | 1 | 0 |
| diferente_do | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| atendimento_ | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| cancelamento | 0 | 0 | 0 | 0 | 1 | 4 | 1 | 0 |
| outro | 0 | 1 | 0 | 1 | 0 | 0 | 2 | 0 |
| sem_problema | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |

## zero_shot

Base do custo: tokens x preço do LLM. Roteamento: com confiança mínima 0.95, 77% dos tickets são classificados automaticamente, com acurácia de 87.0% (meta 85%); o resto vai para revisão humana.

| Categoria | Precisão | Recall | F1 | Suporte |
| --- | ---: | ---: | ---: | ---: |
| problema_entrega | 0.89 | 0.77 | 0.83 | 31 |
| produto_errado_ou_incompleto | 0.89 | 0.89 | 0.89 | 28 |
| produto_defeituoso_ou_qualidade | 0.94 | 0.84 | 0.89 | 19 |
| diferente_do_anuncio | 0.25 | 0.67 | 0.36 | 3 |
| atendimento_vendedor | 0.00 | 0.00 | 0.00 | 2 |
| cancelamento_ou_cobranca | 0.50 | 0.67 | 0.57 | 6 |
| outro | 0.00 | 0.00 | 0.00 | 4 |
| sem_problema | 1.00 | 1.00 | 1.00 | 7 |

| Fatia | n | Acurácia |
| --- | ---: | ---: |
| curtos (<= 30 caracteres) | 16 | 87.5% |
| longos (> 300 caracteres) | 0 | n/d |
| mais de um problema | 32 | 68.8% |
| um problema só | 68 | 82.4% |

Matriz de confusão (linhas: humano; colunas: previsto):

| | problema_ent | produto_erra | produto_defe | diferente_do | atendimento_ | cancelamento | outro | sem_problema |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| problema_ent | 24 | 2 | 0 | 1 | 0 | 4 | 0 | 0 |
| produto_erra | 1 | 25 | 1 | 1 | 0 | 0 | 0 | 0 |
| produto_defe | 0 | 0 | 16 | 3 | 0 | 0 | 0 | 0 |
| diferente_do | 0 | 0 | 0 | 2 | 0 | 0 | 1 | 0 |
| atendimento_ | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| cancelamento | 0 | 0 | 0 | 0 | 0 | 4 | 2 | 0 |
| outro | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 |
| sem_problema | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
