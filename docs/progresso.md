# Progresso

| Fase | Status | Data |
| --- | --- | --- |
| 0. Contas e ambiente | Concluída | 2026-10-31 |
| 1. Fundação e dados | Concluída | 2026-10-31 |
| 2. Modelo de risco | Concluída | 2026-10-31 |
| 3. Causal e A/B | Concluída | 2026-10-31 |
| 4. Taxonomia e rotulagem | Em andamento (rotulagem humana) | |
| 5. Triagem | Código pronto; aguarda o ouro humano | |
| 6. Copiloto, guardrails e API | Em andamento (parte A: copiloto e guardrails) | |
| 7. Avaliação | Pendente | |
| 8. n8n e painel (inclui redesenho visual) | Pendente | |
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

## Fase 1: fundação e dados (2026-10-31)

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

Uma segunda execução terminou sem o `KeyboardInterrupt` da primeira (que veio do terminal, depois dos 65 passos concluídos). CI verde no GitHub.

**Pendências:** nenhuma.

## Fase 2: modelo de risco (2026-10-31)

**O que foi feito**
- `src/copiloto/ds/risk/`: features e proteção contra vazamento (`features.py`), divisão temporal (`split.py`), regra simples, regressão logística e LightGBM (`models.py`), calibração (`calibration.py`), limiar por custo (`threshold.py`), métricas com bootstrap (`evaluate.py`), SHAP (`explain.py`), pipeline e relatório (`pipeline.py`, `report.py`).
- `scripts/train_risk.py` gera `eval/results/risk_metrics.json`, `docs/model-cards/risco-resultados.md` e os gráficos em `docs/figures/risk/`.
- Testes com dados sintéticos (`tests/fakes/risk_data.py`): vazamento, divisão temporal, limiar calculado à mão, calibração e pipeline de ponta a ponta.
- ADR 0005 (limiar por custo).

**Testes no ambiente de desenvolvimento:** `ruff check .` limpo, `ruff format .` aplicado e `pytest`: 58 testes passando.

**Resultados na base real** (teste temporal, 14.374 pedidos de 29/06 a 17/10/2018):
- PR-AUC: regra "atrasou" 0,156; logística 0,290; LightGBM 0,343 (+0,187 sobre a regra, IC 95% +0,167 a +0,208).
- Calibração de Platt: ECE de 0,0154 para 0,0068.
- Limiar por custo: 0,41. No teste, 549 contatos, 59,9% de precisão e R$ 876 de valor líquido, contra R$ 18 da regra "contatar atrasados".
- Model card: `docs/model-cards/risco.md`.

**Pendências**
- Efeito do contato (20%) é premissa. Será tratado no desenho do A/B (Fase 3).
- Análise de equidade por estado: registrada como limitação.

## Fase 3: análise causal e desenho do A/B (2026-10-31)

**O que foi feito**
- `src/copiloto/ds/causal/`: confundidores e matriz de desenho (`data.py`), propensão e sobreposição (`propensity.py`), diferença ingênua, IPW e pareamento implementados à mão (`estimators.py`), balanceamento por SMD (`balance.py`), E-value (`sensitivity.py`), análise com bootstrap (`analysis.py`) e relatório (`report.py`).
- `src/copiloto/ds/experiment/`: tamanho de amostra e duração (`power.py`), sorteio determinístico por hash (`assignment.py`), análise planejada (`analysis.py`), simulação com efeito conhecido (`simulate.py`) e desenho a partir do modelo de risco (`design.py`).
- `scripts/causal_analysis.py` e `scripts/ab_design.py`.
- Testes com dados sintéticos de efeito conhecido: a diferença ingênua exagera o efeito, enquanto IPW e pareamento recuperam o valor verdadeiro. Também testados: fórmula do tamanho de amostra, sorteio estável e balanceado, falso positivo perto de 5% na simulação.
- ADR 0006 (IPW e pareamento à mão).

**Testes no ambiente de desenvolvimento:** `ruff check .` limpo, `ruff format .` aplicado e `pytest`: 79 testes passando.

**Resultados na base real**
- Efeito do atraso na chance de nota negativa (ATT): IPW +45,3 p.p. (IC 95% +44,1 a +46,3), pareamento +45,2 p.p., diferença ingênua +44,8 p.p. O ajuste quase não muda o número, porque os confundidores observados explicam pouco.
- Balanceamento: o maior |SMD| caiu de 0,258 para 0,022 (IPW). Sobreposição completa. E-value 11,8.
- 453 negativas a mais a cada 1.000 atrasos (IC 441 a 463), cerca de 3.469 na base.
- A/B: 8,4 pedidos elegíveis por dia, linha de base de 63,6%. Para 20% de redução, 237 por grupo (57 dias); para 10%, 221 dias. Simulação: 4,6% de falso positivo e IC com cerca de 95% de cobertura.
- Documentos: `docs/analise-causal.md` e `docs/experimento-ab.md`.

**Pendências**
- O registro dos grupos no banco fica para a Fase 6 (`POST /risk/batch`), que usa `assign_group`.

## Fase 4: taxonomia e rotulagem humana (em andamento)

**O que foi feito**
- Leitura de 100 reclamações sorteadas (`scripts/sample_for_taxonomy.py`, semente 7) e taxonomia fechada com o Eduardo: 9 categorias (ADR 0007).
- Guia de rótulos com definições, exemplos fictícios, casos de fronteira e a regra de urgência: `data/labels/guia-de-rotulos.md`.
- `src/copiloto/ai/taxonomy.py` (categorias e urgência por regra) e `src/copiloto/ai/labeling/` (amostragem estratificada, conjunto ouro, kappa).
- Ferramenta de rotulagem em Streamlit, com atalhos de teclado, pular e desfazer: `src/copiloto/dashboard/labeling_app.py`.
- `scripts/make_gold_sample.py` (300 itens: 100 validação, 200 teste, 50 para repetir) e `scripts/labeler_agreement.py` (kappa).

**Testes no ambiente de desenvolvimento:** `ruff check .` limpo, `ruff format .` aplicado e `pytest`: 115 testes passando (inclui a ferramenta de rotulagem de ponta a ponta com `AppTest` e o cliente do LLM com HTTP simulado).

- Rotulagem fraca com LLM pronta para rodar (`scripts/weak_label.py`): 4.000 reclamações (sem as do ouro e as da taxonomia), lotes de 20 por chamada, cache em disco, validação do JSON com Pydantic, retomada de onde parou e estimativa antes de chamar (ADR 0008).
- Cliente do LLM (`src/copiloto/integrations/llm.py`) com cache, novas tentativas em limite de taxa e em erro 5xx, e erros sem detalhes sensíveis; `ScriptedLLM` para os testes.
- **Conjunto prata gerado** (autorizado pelo Eduardo, depois de estimativa e piloto): 4.000 reclamações, prompt `weak-v2`, 0 lotes inválidos, custo real R$ 0. Distribuição: errado ou incompleto 946, não recebido 707, defeito ou qualidade 592, atraso 555, diferente do anúncio 338, sem problema 302, cancelamento ou cobrança 251, outro 235, atendimento 74. Detalhes no ADR 0008 e em `eval/results/weak_label_run.json`.

**Pendências para fechar a fase**
- O Eduardo rotula os 300 itens (rodada 1) e, 7 dias depois, os 50 repetidos (rodada 2).
- Kappa do rotulador.
- Interpretar o conjunto prata contra o ouro na Fase 5 (concordância do LLM com os rótulos humanos).

## Plano adicional pedido pelo Eduardo

- **Redesenho visual** da ferramenta de rotulagem e do painel de métricas, para não parecerem um Streamlit padrão: identidade visual própria (paleta, tipografia), layout em cartões, hierarquia clara, estados vazios e feedback de ação. Será feito na Fase 8, junto com o painel e antes da gravação do vídeo, e revisado com prints antes de fechar a fase.

## Fase 5: triagem (código adiantado em paralelo à rotulagem)

**O que foi feito**
- `src/copiloto/ai/triage/`: contrato comum (`base.py`), zero-shot com LLM e saída validada (`zero_shot.py`, prompt `triage-zs-v1`, já com a regra "não chegou ainda é `nao_recebido`" vinda da revisão do prata), embeddings + regressão logística (`embeddings_lr.py`), métricas de qualidade, latência, custo, robustez e roteamento por confiança (`metrics.py`, `compare.py`), leitura do prata e do ouro (`data.py`).
- `scripts/train_triage_embeddings.py`, `scripts/evaluate_triage.py` (o teste exige `--final`; o LLM exige `--allow-llm`) e `scripts/export_for_colab.py`.
- `notebooks/02-bertimbau-colab.ipynb`: ajuste fino no Colab, previsões devolvidas para avaliação local.
- ADR 0009 (protocolo da comparação, definido antes dos resultados).

**Pendências**
- Ouro humano completo (Fase 4) para avaliar na validação e, por último, no teste.
- Treinar a triagem por embeddings no PC (baixa o modelo do HuggingFace).
- Rodar o zero-shot no ouro (com autorização: 100 chamadas na validação e 200 no teste).
- BERTimbau no Colab.
- Decisão de produção registrada no ADR 0009 e no model card.

## Fase 6: copiloto, guardrails e API (em andamento)

**Parte A: copiloto e guardrails**
- 10 políticas **fictícias** da Loja Exemplo em `policies/` (cada uma com o aviso de ficção e a lista de ações permitidas), divididas em 26 trechos.
- Busca vetorial: `integrations/vectorstore.py` (ChromaDB persistente e versão em memória) e `ai/copilot/retrieve.py`. A consulta junta a descrição da categoria da triagem ao texto do cliente.
- Os 6 guardrails da seção 8.4, determinísticos e em código (`ai/guardrails/`): dados pessoais, prompt injection, ação permitida pela política, promessas sem base, citação obrigatória e tamanho e tom. Cada um tem testes.
- Rascunho (`ai/copilot/draft.py`, prompt `draft-v1`): mascara dados pessoais **antes** do LLM, detecta injection, recupera as políticas, gera a saída estruturada (resposta, políticas citadas, ação, precisa de humano, motivo) e aplica os guardrails de saída. Promessa inventada troca a resposta pelo texto de encaminhamento.
- `scripts/index_policies.py` para indexar e testar a busca. ADR 0010.

**Testes:** `ruff check .` limpo, `ruff format .` aplicado e `pytest`: 169 testes passando, todos com o LLM falso.

**Próximo (parte B):** banco operacional, API (`/triage`, `/draft`, `/feedback`, `/risk/batch`, `/metrics`), idempotência, tabela `llm_calls` e testes de contrato.
