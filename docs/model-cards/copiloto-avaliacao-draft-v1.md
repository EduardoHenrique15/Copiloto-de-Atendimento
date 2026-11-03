# Copiloto: avaliação

Gerado por `scripts/evaluate_copilot.py`. Não edite à mão.

Casos: 60 (fictícios, `eval/copilot_cases.yaml`). Prompt do rascunho: `draft-v1`. Prompt do juiz: `judge-v1`. Modelo: `gemini-3.5-flash-lite`.

## Verificações automáticas (sem LLM)

| Verificação | n | Acerto |
| --- | ---: | ---: |
| Citação de uma política esperada | 60 | 81.7% |
| Ação entre as aceitas | 60 | 88.3% |
| Envio para humano como esperado | 18 | 83.3% |
| Injection detectada pelo guardrail | 10 | 50.0% |

Guardrails: 23.3% dos rascunhos tiveram ao menos um evento; 0.0% tiveram a resposta trocada pelo texto de encaminhamento.

| Evento | Rascunhos |
| --- | ---: |
| missing_citation | 7 |
| pii_masked | 3 |
| prompt_injection | 5 |

Custo de referência (preço pago): rascunho R$ 3.20 por 1.000; juiz R$ 3.68 por 1.000. Latência do rascunho: p50 1400 ms, p95 2067 ms.

## Juiz LLM (rubrica fixa)

Rascunhos julgados: 60 (falhas de formato: 0).

| Critério | Aprovação |
| --- | ---: |
| fidelidade | 93.3% |
| acao | 95.0% |
| citacao | 86.7% |
| tom | 98.3% |
| sem_promessa | 100.0% |
| todos os 5 | 78.3% |

## Concordância juiz × avaliação humana

Rascunhos avaliados pelos dois: 40. Concordância geral 82.5%, kappa 0.15. Regra (ADR 0011): concordância de pelo menos 80% e kappa de pelo menos 0.40. Resultado: **NÃO aceitável**.

| Critério | Concordância | Kappa | Aprovação humana | Aprovação do juiz |
| --- | ---: | ---: | ---: | ---: |
| fidelidade | 75.0% | 0.06 | 77.5% | 92.5% |
| acao | 67.5% | 0.13 | 65.0% | 92.5% |
| citacao | 82.5% | 0.12 | 87.5% | 90.0% |
| tom | 100.0% | 1.00 | 97.5% | 97.5% |
| sem_promessa | 87.5% | 0.00 | 87.5% | 100.0% |

Como a concordância não atingiu a regra, os números do juiz acima não devem ser usados como medida de qualidade.
