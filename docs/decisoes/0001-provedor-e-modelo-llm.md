# ADR 0001: provedor e modelo do LLM

- Status: aceita
- Data: 2026-10-31

## Contexto

O projeto precisa de um LLM para a triagem zero-shot, a rotulagem fraca, o copiloto e o LLM como juiz. A especificação pede um endpoint compatível com OpenAI (Gemini ou Groq), para que o provedor possa ser trocado só pela configuração. O orçamento é zero: só o nível gratuito.

## Opções consideradas

Limites do nível gratuito do Gemini, vistos no AI Studio em 2026-10-31:

| Modelo | RPM | RPD |
| --- | ---: | ---: |
| `gemini-3.5-flash-lite` | 15 | 500 |
| `gemini-3.8-flash` | 5 | 20 |

O `gemini-3.8-flash` é mais novo, mas o limite de 20 requisições por dia não comporta a triagem, a rotulagem fraca nem as demonstrações.

## Decisão

- Modelo padrão: `gemini-3.5-flash-lite`, pelo endpoint `https://generativelanguage.googleapis.com/v1beta/openai/`.
- Reserva: Groq (`https://api.groq.com/openai/v1`), usado se a cota do Gemini acabar.
- A rotulagem fraca (Fase 4) vai enviar vários comentários por chamada (cerca de 20) para caber no limite diário. O tamanho do lote e o impacto na qualidade serão registrados na própria fase.
- O modelo do LLM como juiz será decidido na Fase 7. O `gemini-3.8-flash` é candidato, porque 40 rascunhos cabem em 2 dias.

## Consequências

- Os limites podem mudar. O cache em disco e a troca de provedor pela configuração reduzem esse risco.
- Os números de custo e latência dependem do provedor. Todo relatório registra o modelo e a data.
