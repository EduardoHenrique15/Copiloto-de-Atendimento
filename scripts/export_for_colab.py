"""Exporta os textos para treinar e rodar o BERTimbau no Google Colab.

Gera em data/processed/colab/ (fora do git, são textos da Olist):
    silver_train.csv   complaint_id, text, label          (treino, rótulos do LLM)
    gold_val.csv       complaint_id, text                 (sem rótulos)
    gold_test.csv      complaint_id, text                 (sem rótulos)

Os rótulos humanos do ouro NÃO vão para o Colab: a avaliação é feita aqui,
por scripts/evaluate_triage.py, com as previsões que o notebook devolve.

Uso: python scripts/export_for_colab.py
"""

from pathlib import Path

import pandas as pd

from copiloto.ai.triage.data import load_silver, with_texts
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    labels_dir = ROOT / "data" / "labels"
    out = settings.processed_dir / "colab"
    out.mkdir(parents=True, exist_ok=True)

    silver = load_silver(labels_dir, settings.duckdb_path)
    silver[["complaint_id", "text", "label"]].to_csv(out / "silver_train.csv", index=False)
    sample = pd.read_csv(labels_dir / "gold_sample.csv")
    for split in ("val", "test"):
        ids = sample.loc[sample["split"] == split, ["complaint_id"]]
        with_texts(ids, settings.duckdb_path).to_csv(out / f"gold_{split}.csv", index=False)
    print(f"Arquivos em {out}: silver_train.csv, gold_val.csv, gold_test.csv")


if __name__ == "__main__":
    main()
