"""Calcula amostra, duração e simulações do teste A/B do contato proativo.

Precisa do modelo de risco salvo pela Fase 2 (models/risk/risk_model.joblib).

Saídas:
    eval/results/ab_design.json
    docs/experimento-ab-resultados.md

Uso: python scripts/ab_design.py
"""

import argparse
import json
from pathlib import Path

from copiloto.core.config import get_settings
from copiloto.ds.experiment.design import build_design, eligible_pool, score_orders
from copiloto.ds.experiment.report import render
from copiloto.ds.risk.features import load_risk_frame

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duckdb", type=Path, default=settings.duckdb_path)
    parser.add_argument(
        "--model", type=Path, default=ROOT / "models" / "risk" / "risk_model.joblib"
    )
    parser.add_argument("--n-sims", type=int, default=500)
    args = parser.parse_args()

    df = load_risk_frame(args.duckdb)
    p, threshold = score_orders(args.model, df)
    trained_until = json.loads(
        (ROOT / "eval" / "results" / "risk_metrics.json").read_text(encoding="utf-8")
    )["split"]["val_start"]
    pool = eligible_pool(df, p, threshold, start=trained_until)
    design = build_design(pool, seed=settings.ab_seed, n_sims=args.n_sims)

    path = ROOT / "eval" / "results" / "ab_design.json"
    path.write_text(json.dumps(design, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    out = ROOT / "docs" / "experimento-ab-resultados.md"
    out.write_text(render(design), encoding="utf-8")
    for row in design["plan"]:
        print(
            f"Redução {row['relative_reduction']:.0%}: {row['n_per_group']} por grupo, "
            f"{row['days']:.0f} dias"
        )
    print(f"Relatório: {out}")


if __name__ == "__main__":
    main()
