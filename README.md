# Copiloto de Atendimento

Projeto de portfólio que simula o trabalho de um time de ciência de dados e engenharia de IA numa loja online brasileira: prever avaliações negativas antes que aconteçam, medir quanto o atraso de entrega custa e ajudar o atendimento com triagem automática e rascunhos de resposta.

> Em construção. O andamento de cada fase está em [`docs/progresso.md`](docs/progresso.md).

## Dados

[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce), distribuído no Kaggle sob a licença **CC BY-NC-SA 4.0**. Os arquivos brutos **não** estão neste repositório: baixe-os e coloque os 9 CSVs em `data/raw/`.

## Como rodar (Windows, PowerShell)

Pré-requisito: Python 3.11.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -e .
Copy-Item .env.example .env   # depois preencha os valores
```

Transformar os dados (gera `data/processed/copiloto.duckdb`):

```powershell
python scripts/dbt_build.py
```

Gerar o resumo da análise exploratória (`docs/eda-resumo.md`):

```powershell
python scripts/eda_resumo.py
```

Qualidade:

```powershell
ruff check .
ruff format .
pytest
```

## Licença

Código sob licença MIT. Os dados seguem a licença deles (CC BY-NC-SA 4.0).
