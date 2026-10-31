"""Sorteia 100 reclamações para definir a taxonomia e as mostra no terminal.

Os textos ficam em data/processed/taxonomia/amostra.csv (fora do git: são dados
da Olist) e numa versão legível em data/processed/taxonomia/amostra.txt.
Uso: python scripts/sample_for_taxonomy.py [--n 100]
"""

import argparse
import sys
import textwrap
from pathlib import Path

from copiloto.ai.labeling.sampling import load_complaints, stratified_sample
from copiloto.core.config import get_settings

SEED_TAXONOMY = 7


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duckdb", type=Path, default=settings.duckdb_path)
    parser.add_argument("--n", type=int, default=100)
    args = parser.parse_args()

    sample = stratified_sample(load_complaints(args.duckdb), args.n, seed=SEED_TAXONOMY)
    out = settings.processed_dir / "taxonomia" / "amostra.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(out, index=False, encoding="utf-8")

    lines = []
    for i, row in sample.iterrows():
        late = (
            "sem entrega"
            if row["delay_days"] != row["delay_days"]
            else f"{row['delay_days']:+.0f}d"
        )
        title = f"[{row['comment_title']}] " if isinstance(row["comment_title"], str) else ""
        text = " ".join(f"{title}{row['comment_message']}".split())
        lines.append(
            f"#{i + 1:03d} | nota {row['review_score']} | atraso {late} | {row['order_status']}"
        )
        lines.append(textwrap.indent(textwrap.fill(text, 100), "      "))
    # Arquivo em UTF-8 para não depender da codificação do terminal (PowerShell).
    readable = out.with_suffix(".txt")
    readable.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{len(sample)} reclamações. Arquivos: {out} e {readable}")


if __name__ == "__main__":
    main()
