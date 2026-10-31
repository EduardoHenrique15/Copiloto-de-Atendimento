import numpy as np
import pandas as pd
import pytest

from copiloto.ds.causal.analysis import run_causal
from copiloto.ds.causal.balance import smd
from copiloto.ds.causal.data import as_arrays, design_matrix, prepare
from copiloto.ds.causal.estimators import ipw_effect, ipw_weights, match_att, naive_difference
from copiloto.ds.causal.propensity import fit_propensity
from copiloto.ds.causal.report import render, serializable
from copiloto.ds.causal.sensitivity import e_value, e_value_for_ci
from tests.fakes.causal_data import TRUE_EFFECT, make_causal_frame


@pytest.fixture(scope="module")
def data():
    df = prepare(make_causal_frame())
    x = design_matrix(df)
    t, y = as_arrays(df)
    return df, x, t, y, fit_propensity(x, t)


def test_naive_difference_is_biased_upwards(data):
    _, _, t, y, _ = data
    # Atrasados vêm de longe e de vendedores piores: a diferença ingênua exagera o efeito.
    assert naive_difference(t, y) > TRUE_EFFECT + 0.01


def test_ipw_recovers_true_effect(data):
    _, _, t, y, e = data
    assert ipw_effect(e, t, y, "att")["effect"] == pytest.approx(TRUE_EFFECT, abs=0.02)
    assert ipw_effect(e, t, y, "ate")["effect"] == pytest.approx(TRUE_EFFECT, abs=0.03)


def test_matching_recovers_true_effect(data):
    _, _, t, y, e = data
    m = match_att(e, t, y)
    assert m["effect"] == pytest.approx(TRUE_EFFECT, abs=0.03)
    assert m["n_treated_matched"] + m["n_treated_dropped"] == t.sum()


def test_weighting_improves_balance(data):
    _, x, t, _, e = data
    before = smd(x, t).abs()
    after = smd(x, t, ipw_weights(e, t, "att")).abs()
    assert before["distance_km"] > 0.3
    assert after["distance_km"] < 0.05
    assert after.max() < 0.1


def test_att_weights():
    e = np.array([0.2, 0.5, 0.8])
    t = np.array([1, 0, 0])
    assert np.allclose(ipw_weights(e, t, "att"), [1.0, 1.0, 4.0])
    with pytest.raises(ValueError):
        ipw_weights(e, t, "xyz")


def test_design_matrix_handles_missing_and_rare_categories():
    df = prepare(make_causal_frame(2000))
    df.loc[:9, "seller_prior_avg_score"] = np.nan
    df.loc[:4, "main_category"] = "rara"
    x = design_matrix(df)
    assert not x.isna().any().any()
    assert "seller_prior_avg_score__missing" in x.columns
    assert not any("rara" in c for c in x.columns)


@pytest.mark.parametrize(
    ("rr", "expected"), [(1.0, 1.0), (2.0, 2 + np.sqrt(2)), (0.5, 2 + np.sqrt(2))]
)
def test_e_value_formula(rr, expected):
    assert e_value(rr) == pytest.approx(expected)


def test_e_value_for_ci_crossing_one():
    assert e_value_for_ci(0.95) == 1.0


def test_full_analysis_report():
    df = prepare(make_causal_frame(20000, seed=0))
    report = run_causal(df, n_boot=30)
    ci = report["bootstrap"]["ipw_att"]
    assert ci["ci_low"] < report["estimates"]["ipw_att"] < ci["ci_high"]
    # Com amostra finita o efeito realizado varia; a estimativa fica a ~1 erro-padrão dele.
    assert abs(report["estimates"]["ipw_att"] - TRUE_EFFECT) < 3 * ci["se"]
    assert report["sensitivity"]["e_value"] > 1
    assert report["business"]["extra_negatives_per_1000_late"] == pytest.approx(
        1000 * report["estimates"]["ipw_att"]
    )
    md = render(report)
    assert "Cada 1.000 pedidos atrasados" in md
    assert "propensity" not in serializable(report)


def test_prepare_creates_month_index():
    df = prepare(make_causal_frame(100))
    assert df["purchase_month_index"].min() >= 1
    assert isinstance(df["purchase_month_index"], pd.Series)
