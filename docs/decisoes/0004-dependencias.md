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
| `pandas` | Tabelas em memória para análise e modelos (usado a partir da Fase 2) |

## Desenvolvimento (`requirements-dev.txt`)

| Biblioteca | Por quê |
| --- | --- |
| `pytest` | Testes automatizados |
| `ruff` | Lint e formatação |
| `matplotlib` | Gráficos do notebook de exploração |
| `ipykernel` | Rodar o notebook no VS Code |

As próximas fases acrescentam linhas a esta tabela.
