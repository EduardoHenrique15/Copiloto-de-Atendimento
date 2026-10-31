# Progresso

| Fase | Status | Data |
| --- | --- | --- |
| 0. Contas e ambiente | Concluída | 2026-10-31 |
| 1. Fundação e dados | Em validação (aguarda dbt na base real e CI) | |
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

## Fase 1: fundação e dados (em validação)

**O que foi feito**
- Estrutura de pastas, `pyproject.toml`, `requirements*.txt` com versões fixadas, `.env.example` e LICENSE MIT.
- `src/copiloto/core/`: configuração (`config.py`), logs JSON com correlation id (`logging.py`), erros (`errors.py`) e custo de LLM em reais (`costs.py`), com testes.
- Projeto dbt (`dbt/`): 9 modelos de staging, 7 intermediate e 3 marts (`fct_orders_risk`, `fct_complaints`, `fct_orders_causal`), com 46 testes de qualidade.
- Amostra fictícia em `tests/data/olist/raw` e teste de integração que roda o dbt e confere os marts contra valores calculados à mão, incluindo o histórico as-of do vendedor (anti-vazamento).
- `scripts/dbt_build.py`, `scripts/eda_resumo.py` e `notebooks/01-exploracao.ipynb`.
- CI no GitHub Actions: ruff + pytest.
- ADRs 0003 (DuckDB + dbt) e 0004 (dependências).

**Testes no ambiente de desenvolvimento:** `ruff check .` limpo, `ruff format .` aplicado e `pytest`: 32 testes passando.

**Execução na base real (Windows):** `pytest` com 32 testes passando e `dbt build` com PASS=64, WARN=1, ERROR=0. O aviso é esperado: 4.967 avaliações foram criadas antes da entrega. Números em `docs/eda-resumo.md` e explicados em `docs/aprendizado.md`.

**Pendências para fechar a fase**
- Na primeira execução, o dbt terminou os 65 passos e depois recebeu um `KeyboardInterrupt` sem ação do usuário. Falta confirmar numa segunda execução.
- Confirmar o CI verde no GitHub.
