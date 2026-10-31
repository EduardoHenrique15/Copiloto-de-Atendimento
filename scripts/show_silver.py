"""Mostra rótulos do conjunto prata ao lado dos textos, para revisão humana.

Uso: python scripts/show_silver.py [--n 20]
Grava em data/processed/silver_revisao.txt (UTF-8, fora do git) e imprime o caminho.
"""

import argparse
import textwrap
from pathlib import Path

import pandas as pd

from copiloto.ai.labeling.sampling import load_complaints
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=20, help="primeiros N rótulos")
    args = parser.parse_args()

    silver = pd.read_csv(ROOT / "data" / "labels" / "silver.csv").head(args.n)
    texts = load_complaints(settings.duckdb_path).set_index("complaint_id")
    lines = []
    for i, row in enumerate(silver.itertuples(), start=1):
        complaint = texts.loc[row.complaint_id]
        title = complaint["comment_title"]
        text = f"[{title}] " if isinstance(title, str) else ""
        text = " ".join(f"{text}{complaint['comment_message']}".split())
        multi = " +mais de um" if row.multiple_problems else ""
        lines.append(f"#{i:02d} {row.label}{multi}")
        lines.append(textwrap.indent(textwrap.fill(text, 100), "     "))
    out = settings.processed_dir / "silver_revisao.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(silver)} rótulos. Abra no VS Code: {out}")


if __name__ == "__main__":
    main()
