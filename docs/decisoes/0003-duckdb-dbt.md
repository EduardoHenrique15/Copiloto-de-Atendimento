# ADR 0003: DuckDB + dbt para a camada de dados

- Status: aceita
- Data: 2026-10-31

## Contexto

A base Olist tem 9 CSVs (~126 MB) que precisam ser limpos, juntados e transformados em três tabelas analíticas: risco, reclamações e causal. As transformações precisam ser versionadas, testadas e reproduzíveis por outra pessoa, sem infraestrutura paga.

## Opções consideradas

1. **pandas em scripts Python.** Simples, mas as regras ficam espalhadas em código imperativo, sem testes de qualidade declarativos nem linhagem entre tabelas.
2. **PostgreSQL + dbt.** Funciona, mas exige o banco rodando para qualquer análise.
3. **DuckDB + dbt (`dbt-duckdb`).** Banco analítico em um único arquivo, que lê CSV direto, sem servidor. O dbt dá SQL versionado, camadas, testes e documentação.

## Decisão

DuckDB + dbt Core 1.x (`dbt-duckdb`), com camadas `staging` (tipos e nomes), `intermediate` (junções e agregações) e `marts` (tabelas finais). Os CSVs são lidos como texto (`all_varchar`) e convertidos em staging, para não perder zeros à esquerda dos CEPs. Os testes genéricos (`unique_combination`, `value_between`) foram escritos no próprio projeto para não depender do pacote `dbt_utils`.

O dbt mostra um aviso de que existe o dbt v2. Ficamos no Core 1.x porque é a versão suportada pelo adaptador `dbt-duckdb` instalado.

## Consequências

- Os dados brutos não vão para o git. O CI roda o dbt sobre uma amostra fictícia em `tests/data/olist/raw`, com valores esperados calculados à mão em `tests/integration/test_dbt_marts.py`.
- O PostgreSQL continua sendo o banco operacional da API (Fase 6). O DuckDB é só analítico.
