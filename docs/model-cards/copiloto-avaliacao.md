# Copiloto: avaliação

Gerado por `scripts/evaluate_copilot.py`. Não edite à mão.

Casos: 60 (fictícios, `eval/copilot_cases.yaml`). Prompt do rascunho: `draft-v1`. Prompt do juiz: `n/d`. Modelo: `gemini-3.5-flash-lite`.

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

Custo de referência (preço pago): rascunho R$ 3.20 por 1.000; juiz R$ n/d por 1.000. Latência do rascunho: p50 1400 ms, p95 2067 ms.
