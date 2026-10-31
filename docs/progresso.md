# Progresso

| Fase | Status | Data |
| --- | --- | --- |
| 0. Contas e ambiente | Concluída | 2026-10-31 |
| 1. Fundação e dados | Próxima | |
| 2. Modelo de risco | Pendente | |
| 3. Causal e A/B | Pendente | |
| 4. Taxonomia e rotulagem | Pendente | |
| 5. Triagem | Pendente | |
| 6. Copiloto, guardrails e API | Pendente | |
| 7. Avaliação | Pendente | |
| 8. n8n | Pendente | |
| 9. Documentação e entrega | Pendente | |

## Fase 0: contas e ambiente (2026-10-31)

**O que foi feito**
- Base Olist baixada em `data/raw/` (9 CSVs).
- Chave do Gemini criada e modelo `gemini-3.5-flash-lite` escolhido (ADR 0001). Uma chamada de teste autorizada passou, com saída JSON.
- Chave reserva do Groq criada.
- Docker 29.7.2 funcionando e n8n 2.45.7 abrindo em `localhost:5678`.
- Telegram (bot `@copiloto_atendimento_bot` no grupo `Equipe Atendimento`) e Trello (quadro `Copiloto - Fila de Tickets`) escolhidos e criados (ADR 0002).
- Colab com GPU T4 disponível.
- Detalhes em `docs/setup-verificacao.md`.

**Pendências**
- `TEST_EMAIL_TO`, a credencial de e-mail, o `chat_id` do Telegram e a key e o token do Trello ficam para a Fase 8.
- O teste do Groq fica para quando a reserva for necessária.
