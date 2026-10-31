# Teste A/B do contato proativo: números do desenho

Gerado por `scripts/ab_design.py`. Não edite à mão: rode o script de novo.

## População elegível (histórico, fora do período de treino do modelo)

- Pedidos de alto risco (probabilidade ≥ limiar do modelo): 1.458, de 2018-04-27 a 2018-10-17 (174 dias)
- Volume diário médio: 8.4 pedidos
- Taxa negativa nesse grupo (linha de base): 63.6%
- Probabilidade média prevista: 63.8%

## Tamanho de amostra e duração (alfa 5% bilateral, poder 80%, 50/50)

| Redução relativa mínima | Taxa no tratamento | Pedidos por grupo | Total | Dias |
| ---: | ---: | ---: | ---: | ---: |
| 10.0% | 57.2% | 928 | 1.856 | 221 |
| 20.0% | 50.9% | 237 | 474 | 57 |
| 30.0% | 44.5% | 106 | 212 | 25 |

Sorteio determinístico (semente 42): 49.2% dos pedidos elegíveis caem no tratamento.

## Simulação com os dados históricos

Cada simulação sorteia os grupos de novo e aplica um efeito conhecido no tratamento.

| Efeito verdadeiro | Simulações | Pedidos | % significativo | Efeito médio estimado | Cobertura do IC 95% |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.0% | 500 | 1.458 | 4.6% | 0.2% | 95.4% |
| 10.0% | 500 | 1.458 | 73.8% | 10.2% | 96.0% |
| 20.0% | 500 | 1.458 | 100.0% | 20.3% | 95.6% |
| 30.0% | 500 | 1.458 | 100.0% | 30.2% | 96.0% |

Com efeito 0%, "% significativo" é a taxa de falso positivo (esperado: perto de 5%). Com efeito maior que 0, é o poder com o tamanho histórico disponível.
