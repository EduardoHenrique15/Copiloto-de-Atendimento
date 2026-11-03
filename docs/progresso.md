# Progresso

| Fase | Status | Data |
| --- | --- | --- |
| 0. Contas e ambiente | Concluída | 2026-10-31 |
| 1. Fundação e dados | Concluída | 2026-10-31 |
| 2. Modelo de risco | Concluída | 2026-10-31 |
| 3. Causal e A/B | Concluída | 2026-10-31 |
| 4. Taxonomia e rotulagem | Concluída, sem o kappa do rotulador | 2026-11-01 |
| 5. Triagem | Concluída | 2026-11-01 |
| 6. Copiloto, guardrails e API | Concluída | 2026-10-31 |
| 7. Avaliação | Em andamento | |
| 8. n8n e painel (inclui redesenho visual) | Em andamento (falta configurar no PC) | |
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

## Fase 4: taxonomia e rotulagem humana (2026-11-01)

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

**Fechamento**
- Ouro: 300 rótulos humanos da rodada 1 (100 de validação e 200 de teste), todos com categoria válida. Distribuição: errado ou incompleto 71, defeito ou qualidade 52, atraso 51, não recebido 46, cancelamento ou cobrança 22, diferente do anúncio 20, sem problema 19, outro 11, atendimento 8. 30,7% marcados com mais de um problema.
- O prata foi comparado com o ouro na Fase 5 (ADR 0009).
- **A rodada 2 (50 repetidos) não foi feita, por decisão do Eduardo.** O kappa do rotulador consigo mesmo **não foi medido**. É um critério da especificação que fica em aberto e entra como limitação. A melhor evidência disponível sobre consistência é indireta: na Fase 5, textos quase iguais receberam rótulos diferentes na fronteira entre atraso e não recebido (ADR 0007, emenda 2). `scripts/labeler_agreement.py` continua pronto, caso a rodada 2 seja feita no futuro.

## Plano adicional pedido pelo Eduardo

- **Redesenho visual** da ferramenta de rotulagem e do painel de métricas, para não parecerem um Streamlit padrão: identidade visual própria (paleta, tipografia), layout em cartões, hierarquia clara, estados vazios e feedback de ação. Será feito na Fase 8, junto com o painel e antes da gravação do vídeo, e revisado com prints antes de fechar a fase.

## Fase 5: triagem (2026-11-01)

**O que foi feito**
- `src/copiloto/ai/triage/`: contrato comum (`base.py`), zero-shot com LLM e saída validada (`zero_shot.py`, prompt `triage-zs-v1`, já com a regra "não chegou ainda é `nao_recebido`" vinda da revisão do prata), embeddings + regressão logística (`embeddings_lr.py`), métricas de qualidade, latência, custo, robustez e roteamento por confiança (`metrics.py`, `compare.py`), leitura do prata e do ouro (`data.py`).
- `scripts/train_triage_embeddings.py`, `scripts/evaluate_triage.py` (o teste exige `--final`; o LLM exige `--allow-llm`) e `scripts/export_for_colab.py`.
- `notebooks/02-bertimbau-colab.ipynb`: ajuste fino no Colab, previsões devolvidas para avaliação local.
- ADR 0009 (protocolo da comparação, definido antes dos resultados).

**Validação no ouro (2026-11-01)**
- Ouro humano rodada 1 completo: 300 rótulos do Eduardo (`data/labels/gold.csv`).
- `embeddings_lr`: F1 macro 0,560, acurácia 65,0%; roteamento com confiança mínima 0,75 deixa 36% automático, com 86,1% de acerto.
- `zero_shot` (`triage-zs-v1`, 100 chamadas autorizadas, R$ 0): F1 macro 0,532, acurácia 72,0%; a confiança informada pelo LLM não chega a 85% de acerto em nenhum limiar.
- `scripts/show_triage_errors.py` lista os erros da validação com os textos (arquivo fora do git).
- Erro principal do zero-shot: 6 de 19 `atraso_entrega` humanos marcados como `nao_recebido`. O Eduardo decidiu mudar o guia (ADR 0007, emenda): "ainda não chegou" é atraso; não recebido é "consta entregue e não recebi" ou extravio. Prompt `triage-zs-v2`.

- `zero_shot` (`triage-zs-v2`, 100 chamadas autorizadas, R$ 0): F1 macro 0,505, acurácia 70,0%. O erro inverteu (8 de 12 `nao_recebido` saíram como atraso), e a leitura dos erros mostrou rótulos humanos inconsistentes nessa fronteira.
- Decisão do Eduardo (ADR 0007, emenda 2): atraso e não recebido contam como `problema_entrega` na métrica (8 categorias), e o status do pedido separa os dois no serviço de triagem.

- Validação com 8 categorias (sem nova chamada): zero-shot F1 macro 0,568 e acurácia de 78,0% (77% automáticos com 87,0% de acerto); embeddings F1 macro 0,562 e acurácia de 67,0% (36% automáticos com 86,1%).
- **Decisão de produção, antes do teste (ADR 0009):** zero-shot com reserva por embeddings (`ai/triage/fallback.py`), com limiares de 0,95 e 0,75 fixados na validação. BERTimbau fora, por decisão do Eduardo.
- Correção: no teste, o script agora usa o limiar da validação, sem escolher outro no teste.

**Teste final (200 itens, uma execução com `--final`, 200 chamadas autorizadas, R$ 0)**
- Zero-shot (produção): F1 macro 0,738 e acurácia de 83,5%; com o limiar da validação (0,95), 75% dos tickets ficam automáticos, com 92,0% de acerto.
- Embeddings + LR (reserva): F1 macro 0,639 e acurácia de 71,5%; com 0,75, 47% ficam automáticos, com 86,2% de acerto.
- Model card: `docs/model-cards/triagem.md`. Tabelas em `docs/model-cards/triagem-resultados.md`. Resultado registrado no ADR 0009.

**Pendências:** nenhuma desta fase.

## Fase 6: copiloto, guardrails e API (2026-10-31)

**Parte A: copiloto e guardrails**
- 10 políticas **fictícias** da Loja Exemplo em `policies/` (cada uma com o aviso de ficção e a lista de ações permitidas), divididas em 26 trechos.
- Busca vetorial: `integrations/vectorstore.py` (ChromaDB persistente e versão em memória) e `ai/copilot/retrieve.py`. A consulta junta a descrição da categoria da triagem ao texto do cliente.
- Os 6 guardrails da seção 8.4, determinísticos e em código (`ai/guardrails/`): dados pessoais, prompt injection, ação permitida pela política, promessas sem base, citação obrigatória e tamanho e tom. Cada um tem testes.
- Rascunho (`ai/copilot/draft.py`, prompt `draft-v1`): mascara dados pessoais **antes** do LLM, detecta injection, recupera as políticas, gera a saída estruturada (resposta, políticas citadas, ação, precisa de humano, motivo) e aplica os guardrails de saída. Promessa inventada troca a resposta pelo texto de encaminhamento.
- `scripts/index_policies.py` para indexar e testar a busca. ADR 0010.

**Testes:** `ruff check .` limpo, `ruff format .` aplicado e `pytest`: 169 testes passando, todos com o LLM falso.

**Parte B: banco, API e métricas**
- Banco operacional (`src/copiloto/db/`): tickets (texto com dados pessoais já mascarados), rascunhos, decisões, `llm_calls`, eventos de guardrail e grupos do A/B. Migração Alembic `0001`, testada contra os modelos.
- Serviços (`src/copiloto/services/`): triagem com urgência por regra e revisão humana abaixo de `TRIAGE_MIN_CONFIDENCE`; rascunho; decisão do atendente; lote de risco diário com sorteio do A/B gravado e limite diário no tratamento; métricas da seção 8.6.
- API FastAPI (`src/copiloto/api/`): `GET /health`, `POST /triage`, `POST /draft`, `POST /feedback`, `POST /risk/batch` e `GET /metrics`. Chave em `X-API-Key`, entrada e saída validadas por Pydantic (campos extras recusados), idempotência em `/triage` e `/draft` (sem nova chamada ao LLM), erros com mensagem clara e sem traceback, e correlation id no cabeçalho.
- Testes de contrato (`tests/contract/`): formato de cada rota, códigos HTTP, autenticação, idempotência e um snapshot do OpenAPI que falha se o contrato do n8n mudar sem querer.
- `Dockerfile` e `docker-compose.yml` (API e PostgreSQL), `scripts/demo_api.py` para a demonstração com o LLM real.

**Testes:** `pytest` com todos os testes passando, sempre com o LLM falso.

**Demonstração autorizada com o LLM real** (`scripts/demo_api.py --allow-llm`, 1 chamada):
- Reclamação real: "Não entregou nem entra contato".
- Triagem (embeddings + LR, sem LLM): `nao_recebido`, confiança 0,74, urgência média, sem revisão humana.
- Rascunho: respondeu com base na política citada (`pedido-nao-recebido#resultado-da-investigacao`), sem valores ou prazos inventados, nenhum guardrail disparado, ação `nenhuma`, marcado para revisão humana pelo próprio modelo.
- Métricas: 1 chamada, latência de 1,87 s, custo de referência R$ 0,0034 (real: R$ 0, plano gratuito).
- Observação: o rascunho diz "já estamos investigando", uma promessa de ação sem número que o guardrail de promessas não pega. É a limitação já registrada no ADR 0010; a avaliação da Fase 7 mede quantas vezes isso acontece.

**Pendências:** nenhuma desta fase. A qualidade dos rascunhos é medida na Fase 7.

## Fase 7: avaliação (em andamento)

**O que foi feito**
- 60 casos fictícios do copiloto (`eval/copilot_cases.yaml`): 9 categorias, 7 sem política aplicável, 10 tentativas de prompt injection e 3 com dados pessoais inventados.
- `src/copiloto/ai/eval/`: leitura e validação dos casos, verificações automáticas, juiz LLM com rubrica fixa (`judge-v1`), concordância juiz × humano (kappa), execução incremental e relatório.
- `scripts/evaluate_copilot.py`: etapas `drafts` e `judge` (cada uma exige `--allow-llm`, com estimativa antes) e relatório em `docs/model-cards/copiloto-avaliacao.md`.
- Ferramenta de avaliação humana às cegas: `streamlit run src/copiloto/dashboard/copilot_eval_app.py` (40 rascunhos sorteados).
- Regressão no CI: 8 casos com respostas gravadas (`eval/regression_cases.yaml`, `tests/unit/test_copilot_regression.py`).
- ADR 0011, com a regra de aceitação do juiz definida antes dos resultados.

**Pendências**
- Rodar os rascunhos (60 chamadas, com autorização).
- Avaliação humana dos 40 rascunhos, antes do juiz.
- Rodar o juiz (60 chamadas, com autorização) e medir a concordância.
- Resumo no README.

## Fase 8: n8n, painel e redesenho (em andamento)

**O que foi feito**
- `docker-compose.yml` com o n8n 2.45.7 (volume `n8n_data` da Fase 0 reaproveitado) e o painel. O n8n recebe só as variáveis de que precisa.
- Os 4 fluxos em `n8n/workflows/`: triagem, aprovação humana, contato proativo e monitoramento (ADR 0012).
  - Foram testados num n8n 2.45.7 local, de ponta a ponta, com a API sobre o container de teste e dublês do Telegram, do Trello e do e-mail.
- `scripts/simulate_tickets.py` envia reclamações reais (fora do ouro) ao webhook.
- API:
  - `GET /metrics/report`: relatório semanal em texto, sem LLM;
  - `text_masked` na resposta da triagem;
  - snapshot do contrato atualizado.
- Painel de métricas (`src/copiloto/dashboard/metrics_app.py`): operação ao vivo, com alertas pelos limites `ALERT_*`, e a qualidade medida offline.
- Redesenho visual (`src/copiloto/dashboard/theme.py` e `.streamlit/config.toml`):
  - tipografia IBM Plex, paleta própria e cartões;
  - aplicado ao painel, à ferramenta de rotulagem e à de avaliação.
- `tests/unit/test_n8n_exports.py` confere que os JSON não têm segredos.
- `n8n/README.md` traz o passo a passo de configuração.

**Pendências (no PC do Eduardo)**
- Credenciais no n8n, `chat_id` do Telegram, listas e código do quadro do Trello, `TEST_EMAIL_TO` e senha de app do Gmail.
- Importar e ativar os fluxos e simular 2 reclamações (com autorização: cerca de 4 chamadas ao LLM).
- Critério de pronto da especificação: uma reclamação percorre triagem, rascunho, aprovação e e-mail; o fluxo proativo registra grupos; o alerta dispara com o limite forçado.
