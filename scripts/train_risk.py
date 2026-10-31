"""Treina e avalia o modelo de risco na base real e grava os resultados.

Saídas:
    eval/results/risk_metrics.json         números completos
    docs/model-cards/risco-resultados.md   tabelas para o model card
    docs/figures/risk/*.png                gráficos
    models/risk/risk_model.joblib          modelo (fora do git)

Uso: python scripts/train_risk.py
"""

import argparse
from pathlib import Path

from copiloto.core.config import get_settings
from copiloto.ds.risk.features import load_risk_frame
from copiloto.ds.risk.pipeline import run_pipeline
from copiloto.ds.risk.report import render
from copiloto.ds.risk.threshold import CostAssumptions

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--duckdb", type=Path, default=settings.duckdb_path)
    args = parser.parse_args()

    assumptions = CostAssumptions(
        contact_cost_brl=settings.risk_contact_cost_brl,
        negative_review_cost_brl=settings.risk_negative_review_cost_brl,
        contact_effect=settings.risk_assumed_contact_effect,
    )
    df = load_risk_frame(args.duckdb)
    report = run_pipeline(
        df,
        assumptions,
        figures_dir=ROOT / "docs" / "figures" / "risk",
        results_path=ROOT / "eval" / "results" / "risk_metrics.json",
        model_path=ROOT / "models" / "risk" / "risk_model.joblib",
    )
    out = ROOT / "docs" / "model-cards" / "risco-resultados.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(report), encoding="utf-8")

    test = report["metrics_test"]
    print(
        f"PR-AUC teste: baseline {test['baseline']['pr_auc']:.3f} | "
        f"logística {test['logistic']['pr_auc']:.3f} | "
        f"LightGBM {test['lightgbm']['pr_auc']:.3f}"
    )
    print(f"Limiar: {report['threshold_val']['threshold']:.2f}")
    print(f"Relatório: {out}")


if __name__ == "__main__":
    main()
