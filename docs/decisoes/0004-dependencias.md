# ADR 0004: dependências e justificativas

Regra do projeto: toda biblioteca tem uma linha dizendo por que existe. Versões fixadas em `requirements*.txt`.

## Execução (`requirements.txt`)

| Biblioteca | Por quê |
| --- | --- |
| `pydantic` | Validação de dados e de configuração |
| `pydantic-settings` | Lê e valida o `.env` na inicialização |
| `structlog` | Logs em JSON com correlation id |
| `duckdb` | Banco analítico em arquivo, lido pelos scripts e notebooks |
| `dbt-core`, `dbt-duckdb` | Transformações SQL versionadas e testadas (ADR 0003) |
| `pandas` | Tabelas em memória para análise e modelos |
| `scikit-learn` | Regressão logística, pré-processamento, calibração e métricas (Fase 2) |
| `lightgbm` | Modelo de gradiente para dados tabulares (Fase 2) |
| `shap` | Explicação global e por pedido do modelo de risco (Fase 2). Versão 0.51.0 porque as seguintes exigem Python 3.12 |
| `joblib` | Salvar e carregar o modelo treinado (Fase 2) |
| `statsmodels` | Poder estatístico, tamanho de amostra e teste de duas proporções do A/B (Fase 3) |
| `streamlit` | Ferramenta de rotulagem humana (Fase 4) e painel de métricas (Fase 8) |
| `openai` | SDK para o endpoint compatível com OpenAI (Gemini, Groq): provedor trocável pelo `.env` (Fase 4) |
| `streamlit-shortcuts` | Atalhos de teclado na rotulagem (1 a 9, m, p, z): rotular 350 itens só com o mouse é lento e cansativo |
| `matplotlib` | Gráficos gerados pelos scripts (curvas PR, confiabilidade, valor e SHAP). Saiu do `requirements-dev.txt` porque os scripts de relatório usam |

## Desenvolvimento (`requirements-dev.txt`)

| Biblioteca | Por quê |
| --- | --- |
| `pytest` | Testes automatizados |
| `respx` | Simula as respostas HTTP do LLM nos testes, sem rede e sem gastar cota |
| `ruff` | Lint e formatação |
| `ipykernel` | Rodar o notebook no VS Code |

As próximas fases acrescentam linhas a esta tabela.
