# Relatório de impacto

Gerado por `scripts/impact_report.py` a partir de `eval/results/`. Não edite à mão.

Os valores em reais dependem de **premissas** (abaixo), que não foram medidas. A base é a Olist de 2016 a 2018, e as políticas e os custos da loja são fictícios.

## Premissas

| Premissa | Valor | Origem |
| --- | ---: | --- |
| Custo de uma avaliação negativa | R$ 30 | Premissa (ADR 0005) |
| Custo de um contato proativo | R$ 2 | Premissa (ADR 0005) |
| Avaliações negativas evitadas pelo contato | 20% | Premissa; é o que o teste A/B mediria |

## 1. Quanto o atraso custa

- Efeito causal do atraso (IPW, ATT): **+45,3 pontos percentuais** na chance de nota 1 ou 2 (IC 95% de 44,1 a 46,3).
- São **453 avaliações negativas a mais a cada 1.000 pedidos atrasados**.
- Na base: 7.661 pedidos atrasados, de 95.824 avaliados, geraram cerca de **3.469 negativas a mais** (IC de 3.376 a 3.548).
- Com a premissa de R$ 30 por negativa: cerca de **R$ 104.070** no período inteiro da base.

## 2. Contato proativo com o modelo de risco

Período de teste: 110 dias, 14.374 pedidos entregues. Valor líquido = negativas evitadas × custo da negativa − contatos × custo do contato.

| Política | Contatos | Negativas alcançadas | Precisão | Valor líquido |
| --- | ---: | ---: | ---: | ---: |
| Modelo no limiar | 549 | 329 | 59,9% | R$ 876 |
| Contatar todo pedido atrasado | 1.017 | 342 | 33,6% | R$ 18 |
| Contatar todos | 14.374 | 1.420 | 9,9% | −R$ 20.228 |
| Não contatar ninguém | 0 | 0 | 0,0% | R$ 0 |

- O modelo gera cerca de **R$ 239 a cada 30 dias** no volume da base, contra quase zero da regra simples. Contatar todos dá prejuízo.
- O ganho depende inteiramente do efeito do contato, que é premissa. Por isso, o próximo passo é o teste A/B, e não escalar o contato.

## 3. Quanto tempo o teste A/B leva

Com 8,4 pedidos elegíveis por dia:

| Queda que o teste detecta | Pedidos por grupo | Duração |
| --- | ---: | ---: |
| 10% | 928 | 221 dias |
| 20% | 237 | 57 dias |
| 30% | 106 | 25 dias |

## 4. Atendimento: triagem e copiloto

- **Triagem (zero-shot, teste):** acurácia de 83,5% contra rótulos de referência (feitos com apoio de IA, ADR 0013). 75% dos tickets são classificados sozinhos, com 92,0% de acerto. Custo de referência: R$ 1,64 por 1.000 tickets.
- **Copiloto (draft-v3, 60 casos fictícios):** cita a política esperada em 98,3% e sugere uma ação aceita em 98,3%. Custo de referência: R$ 3,89 por 1.000 rascunhos.
- O ganho em tempo de atendimento não foi medido: não há dados de tempo por ticket na base.
