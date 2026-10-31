"""Calcula o kappa do rotulador (rodada 1 x rodada 2) e grava
eval/results/labeler_kappa.json.

Uso: python scripts/labeler_agreement.py
"""

import json
from pathlib import Path

from copiloto.ai.labeling.gold import GoldStore, self_agreement

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = self_agreement(GoldStore(ROOT / "data" / "labels" / "gold.csv").load())
    out = ROOT / "eval" / "results" / "labeler_kappa.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Itens: {result['n']} | concordância bruta: {result['raw_agreement']:.1%} | "
        f"kappa: {result['kappa']:.3f}"
    )
    for d in result["disagreements"]:
        print(f"  {d['complaint_id'][:8]}: {d['round_1']} -> {d['round_2']}")


if __name__ == "__main__":
    main()
