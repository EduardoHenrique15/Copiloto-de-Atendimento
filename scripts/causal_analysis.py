"""Estima o efeito causal do atraso na avaliação e grava os resultados.

Saídas:
    eval/results/causal.json
    docs/analise-causal-resultados.md
    docs/figures/causal/*.png

Uso: python scripts/causal_analysis.py [--n-boot 200]
O bootstrap reajusta a propensão em cada reamostra; 200 reamostras levam alguns minutos.
"""

import argparse
import time
from pathlib import Path

from copiloto.core.config import get_settings
from copiloto.ds.causal.analysis import run_causal
from copiloto.ds.causal.data import load_causal_frame
from copiloto.ds.causal.report import plot, render, save_json

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duckdb", type=Path, default=settings.duckdb_path)
    parser.add_argument("--n-boot", type=int, default=200)
    args = parser.parse_args()

    start = time.perf_counter()
    report = run_causal(
        load_causal_frame(args.duckdb),
        n_boot=args.n_boot,
        negative_review_cost_brl=settings.risk_negative_review_cost_brl,
    )
    plot(report, ROOT / "docs" / "figures" / "causal")
    save_json(report, ROOT / "eval" / "results" / "causal.json")
    out = ROOT / "docs" / "analise-causal-resultados.md"
    out.write_text(render(report), encoding="utf-8")

    est = report["estimates"]
    print(
        f"Efeito do atraso na taxa negativa: ingênuo {est['naive']:+.3f} | "
        f"IPW {est['ipw_att']:+.3f} | pareamento {est['matching_att']:+.3f}"
    )
    print(f"Tempo: {time.perf_counter() - start:.0f} s. Relatório: {out}")


if __name__ == "__main__":
    main()
