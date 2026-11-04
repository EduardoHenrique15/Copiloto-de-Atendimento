import json
from pathlib import Path

import pytest

from copiloto.reports.impact import compute, render

RESULTS = Path(__file__).resolve().parents[2] / "eval" / "results"


def _load(name):
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


@pytest.fixture
def numbers():
    return compute(
        _load("risk_metrics.json"),
        _load("causal.json"),
        _load("ab_design.json"),
        _load("triage_comparison_test.json"),
        _load(sorted(RESULTS.glob("copilot_eval_*.json"))[-1].name),
    )


def test_derived_numbers_by_hand(numbers):
    c = numbers["causal"]
    assert c["extra_negatives"] == pytest.approx(c["att"] * c["n_late"])
    assert c["cost_brl"] == pytest.approx(c["extra_negatives"] * 30)
    assert c["extra_negatives_low"] < c["extra_negatives"] < c["extra_negatives_high"]
    r = numbers["risk"]
    assert r["value_per_30_days"] == pytest.approx(
        r["policies"]["modelo_no_limiar"]["value_brl"] / r["test_days"] * 30
    )


def test_render_has_sections_and_premises(numbers):
    md = render(numbers)
    for text in [
        "## Premissas",
        "## 1. Quanto o atraso custa",
        "## 2.",
        "## 3.",
        "## 4.",
        "Premissa",
        "Não edite à mão",
    ]:
        assert text in md
