"""Gera docs/relatorio-impacto.md a partir dos resultados versionados (sem LLM, sem dados brutos).

Uso: python scripts/impact_report.py
"""

import json
from pathlib import Path

from copiloto.reports.impact import compute, render

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def main() -> None:
    copilot = sorted(RESULTS.glob("copilot_eval_*.json"))[-1]  # versão mais nova
    numbers = compute(
        load("risk_metrics.json"),
        load("causal.json"),
        load("ab_design.json"),
        load("triage_comparison_test.json"),
        load(copilot.name),
    )
    out = ROOT / "docs" / "relatorio-impacto.md"
    out.write_text(render(numbers), encoding="utf-8")
    print(f"Relatório: {out}")


if __name__ == "__main__":
    main()
