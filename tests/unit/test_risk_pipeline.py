"""Pipeline de ponta a ponta com dados sintéticos (sem a base real)."""

import json

import numpy as np
import pytest

from copiloto.ds.risk.models import LightGBMModel
from copiloto.ds.risk.pipeline import run_pipeline
from copiloto.ds.risk.report import render
from copiloto.ds.risk.split import temporal_split
from copiloto.ds.risk.threshold import CostAssumptions
from tests.fakes.risk_data import make_risk_frame

A = CostAssumptions(contact_cost_brl=2, negative_review_cost_brl=30, contact_effect=0.2)


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("risco")
    df = make_risk_frame(6000, seed=1)
    report = run_pipeline(df, A, out / "fig", out / "metrics.json", model_path=out / "model.joblib")
    return out, report


def test_lightgbm_beats_baseline_on_synthetic_signal(run):
    _, report = run
    m = report["metrics_test"]
    assert m["lightgbm"]["pr_auc"] > m["baseline"]["pr_auc"]
    assert m["lightgbm"]["pr_auc"] > m["lightgbm"]["base_rate"]


def test_outputs_are_written(run):
    out, report = run
    saved = json.loads((out / "metrics.json").read_text(encoding="utf-8"))
    assert saved["threshold_val"] == report["threshold_val"]
    for name in ("pr_curve", "reliability", "value_curve", "shap_global"):
        assert (out / "fig" / f"{name}.png").stat().st_size > 0
    assert (out / "model.joblib").exists()


def test_policies_and_examples(run):
    _, report = run
    assert report["policies_test"]["nao_contatar"]["value_brl"] == 0
    assert set(report["shap_examples"]) == {"alto", "medio", "baixo"}
    probs = [report["shap_examples"][k]["probability"] for k in ("baixo", "medio", "alto")]
    assert probs == sorted(probs)
    assert all(len(e["reasons"]) == 5 for e in report["shap_examples"].values())


def test_report_renders_markdown(run):
    _, report = run
    md = render(report)
    assert md.startswith("# Modelo de risco: resultados")
    assert "PR-AUC" in md and "Limiar escolhido" in md


def test_unseen_category_does_not_break_prediction():
    df = make_risk_frame(3000, seed=2)
    s = temporal_split(df)
    model = LightGBMModel(params={**LightGBMModel().params, "n_estimators": 50}).fit(s.train, s.val)
    new = s.test.head(5).copy()
    new["main_category"] = "categoria_nova"
    p = model.predict_proba(new)
    assert np.all((p >= 0) & (p <= 1))
