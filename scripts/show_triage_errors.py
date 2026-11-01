"""Mostra os erros de uma abordagem de triagem na validação, com os textos.

Só a validação: o teste fica fechado até a comparação final (ADR 0009).
Uso: python scripts/show_triage_errors.py --approach zero_shot
     python scripts/show_triage_errors.py --approach zero_shot \
         --human atraso_entrega --pred nao_recebido
Grava em data/processed/triagem_erros_val_<abordagem>.txt (UTF-8, fora do git).
"""

import argparse
from pathlib import Path

import pandas as pd

from copiloto.ai.triage.compare import format_errors, preds_path
from copiloto.ai.triage.data import load_gold
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--approach", required=True)
    parser.add_argument("--human", help="só erros com este rótulo humano")
    parser.add_argument("--pred", help="só erros com esta previsão")
    args = parser.parse_args()

    path = preds_path(ROOT / "eval" / "results", "val", args.approach)
    if not path.exists():
        raise SystemExit(f"Sem previsões em {path}. Rode scripts/evaluate_triage.py antes.")
    gold = load_gold(ROOT / "data" / "labels", settings.duckdb_path, "val")
    frame = gold.merge(pd.read_csv(path), on="complaint_id", how="inner")
    out = settings.processed_dir / f"triagem_erros_val_{args.approach}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(format_errors(frame, args.approach, args.human, args.pred), encoding="utf-8")
    print(f"Abra no VS Code: {out}")


if __name__ == "__main__":
    main()
