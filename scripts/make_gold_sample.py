"""Sorteia o conjunto ouro (300 reclamações) e grava data/labels/gold_sample.csv.

Exclui as 100 reclamações lidas para definir a taxonomia. O arquivo só tem ids,
divisão (val/test) e a marcação de repetição: pode ir para o git.

Uso: python scripts/make_gold_sample.py
"""

from pathlib import Path

import pandas as pd

from copiloto.ai.labeling.gold import make_gold_sample
from copiloto.ai.labeling.sampling import load_complaints
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    out = ROOT / "data" / "labels" / "gold_sample.csv"
    if out.exists():
        print(f"{out} já existe. Apague-o à mão se quiser sortear de novo.")
        return
    taxonomy_sample = settings.processed_dir / "taxonomia" / "amostra.csv"
    exclude = set(pd.read_csv(taxonomy_sample, usecols=["complaint_id"])["complaint_id"])
    sample = make_gold_sample(load_complaints(settings.duckdb_path), exclude=exclude)
    out.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(out, index=False)
    counts = sample["split"].value_counts().to_dict()
    print(f"{len(sample)} itens ({counts}), {int(sample['repeat'].sum())} para repetir. {out}")


if __name__ == "__main__":
    main()
