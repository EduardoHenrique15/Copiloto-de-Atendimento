# Model card: risco de avaliação negativa

**Resumo:** no dia da entrega, o modelo estima a probabilidade de o pedido receber nota 1 ou 2. No teste temporal, ele encontra os pedidos negativos com PR-AUC de 0,343, contra 0,156 da regra "negativo se atrasou" e 0,099 de um sorteio. Com o limiar por custo, contatar os pedidos sinalizados gerou valor líquido estimado de R$ 876 no período de teste, contra R$ 18 da regra "contatar atrasados". O valor depende de premissas ainda não medidas.

Todos os números vêm de `scripts/train_risk.py`. Tabelas completas em [`risco-resultados.md`](risco-resultados.md) e números brutos em `eval/results/risk_metrics.json`.

## Detalhes do modelo

| Item | Valor |
| --- | --- |
| Tipo | LightGBM (gradient boosting), com calibração de Platt |
| Alvo | `is_negative` = nota de avaliação 1 ou 2 |
| Momento da previsão | Data de entrega ao cliente (`feature_cutoff_at`) |
| Saída | Probabilidade calibrada e os 5 principais motivos (SHAP) |
| Limiar de contato | 0,41 (escolhido por valor esperado na validação) |
| Código | `src/copiloto/ds/risk/` |
| Semente | 42 |

## Uso pretendido

- **Para:** priorizar pedidos para um contato proativo do atendimento (acompanhamento, pedido de desculpas, cupom), antes de o cliente avaliar.
- **Não é para:** punir vendedores, negar serviço a clientes ou decidir sozinho sobre compensações. A decisão de contato passa pelo fluxo do n8n, com limite diário (`PROACTIVE_MAX_PER_DAY`).
- **Neste projeto:** os contatos são simulados e só vão para o e-mail de teste (`TEST_EMAIL_TO`).

## Dados

- Base pública da Olist (Kaggle, CC BY-NC-SA 4.0), já anonimizada.
- `marts.fct_orders_risk`: 95.824 pedidos entregues e avaliados.
- Divisão **temporal** pela data de entrega:

| Parte | Pedidos | Período | Taxa negativa |
| --- | ---: | --- | ---: |
| Treino | 67.020 | 11/10/2016 a 27/04/2018 | 13,5% |
| Validação | 14.184 | 27/04/2018 a 29/06/2018 | 12,4% |
| Teste | 14.374 | 29/06/2018 a 17/10/2018 | 9,9% |

- 246 pedidos foram descartados porque a avaliação deles ainda não existia na data de corte da parte seguinte.

## Features (todas conhecidas até a entrega)

- **Entrega:** dias de atraso em relação à data estimada, se atrasou, dias até a entrega e prazo prometido.
- **Pedido:** itens, produtos e vendedores; valor dos itens; frete e frete relativo; categoria principal; forma de pagamento; parcelas.
- **Geografia:** estado do cliente e do vendedor, se são do mesmo estado, e distância pelo CEP.
- **Histórico do vendedor (as-of compra):** pedidos anteriores, nota média anterior, taxa de atraso anterior.

**Proteção contra vazamento:**
1. A lista de features não pode conter colunas da avaliação.
2. Toda data usada é anterior ou igual à entrega.
3. O histórico do vendedor usa só o passado (teste no dbt).
4. A divisão é temporal, com a regra de rótulo disponível.
Cada item tem teste automatizado.

## Resultados no teste

| Modelo | PR-AUC | ROC-AUC | Brier | ECE |
| --- | ---: | ---: | ---: | ---: |
| Regra "atrasou" | 0,156 | 0,594 | 0,0891 | 0,0307 |
| Regressão logística | 0,290 | 0,712 | 0,0807 | 0,0133 |
| LightGBM | 0,343 | 0,725 | 0,0766 | 0,0154 |
| **LightGBM calibrado** | **0,343** | **0,725** | **0,0764** | **0,0068** |

- Diferença de PR-AUC do LightGBM sobre a regra: **+0,187** (IC 95% por bootstrap: +0,167 a +0,208).
- Sobre a logística: **+0,053** (IC 95%: +0,039 a +0,070).
- A calibração não muda a ordenação (PR-AUC igual), mas reduz o erro de calibração (ECE) de 0,0154 para 0,0068. O ganho de Platt sobre "sem calibração" na validação foi pequeno (Brier 0,0880 contra 0,0882).

## Limiar e valor

Premissas padrão: contato custa R$ 2, evitar uma negativa vale R$ 30 e o contato evita 20% das negativas. Ponto de equilíbrio teórico: p = 0,333. Limiar escolhido na validação: **0,41**.

| Política (teste) | Contatos | Precisão | Recall | Valor líquido |
| --- | ---: | ---: | ---: | ---: |
| **Modelo no limiar 0,41** | 549 | 59,9% | 23,2% | **R$ 876** |
| Contatar todos os atrasados | 1.017 | 33,6% | 24,1% | R$ 18 |
| Contatar todos | 14.374 | 9,9% | 100% | −R$ 20.228 |
| Não contatar | 0 | — | — | R$ 0 |

O modelo alcança praticamente as mesmas negativas que a regra "atrasados" (329 contra 342) com quase metade dos contatos.

**Sensibilidade:** o valor depende só da razão custo ÷ (efeito × valor da negativa). Com contato a R$ 5 e efeito de 20%, nenhum limiar compensa e o melhor é não contatar. Com efeito de 40%, o limiar cai para 0,17 e o valor quadruplica. A tabela completa está em `risco-resultados.md`.

## Explicabilidade

As features mais importantes (média de |SHAP|) são, nesta ordem:
1. dias de atraso;
2. número de itens;
3. dias até a entrega;
4. nota média anterior do vendedor;
5. categoria.

O número de itens em segundo lugar sugere que pedidos com vários itens geram mais reclamações, por exemplo de entrega parcial. Isso é uma hipótese a checar na triagem (Fase 5), não uma conclusão.

O exemplo de **risco alto** (77,7%: 15 dias de atraso, 37 dias até a entrega) recebeu avaliação **não negativa**. Um modelo de risco erra em casos individuais, e por isso o contato é uma ação de baixo custo, não uma punição.

## Limitações

1. **Efeito do contato não medido.** Os 20% são premissa. O valor em reais só vira estimativa real depois do teste A/B (Fase 3).
2. **Mudança de distribuição.** A taxa negativa cai de 13,5% (treino) para 9,9% (teste). O fim de 2018 tem menos atrasos e base menor. O modelo precisa ser monitorado e retreinado.
3. **Período curto e antigo** (2016 a 2018), de um único marketplace.
4. **Recall baixo no limiar:** 23% das negativas são alcançadas. As demais acontecem sem sinal claro na entrega (por exemplo, produto defeituoso entregue no prazo).
5. **Sem análise de equidade.** O estado do cliente é uma feature. Não verificamos se o modelo sinaliza clientes de alguns estados com taxas muito diferentes pelo mesmo motivo. Isso fica como melhoria.
6. **476 pedidos sem distância** (CEP sem coordenada). O LightGBM trata o valor como ausente.
7. O limiar foi escolhido na mesma validação usada para calibrar, o que pode deixar o valor na validação levemente otimista. O teste não foi usado em nenhuma escolha.

## Como reproduzir

```powershell
python scripts/dbt_build.py
python scripts/train_risk.py
```
