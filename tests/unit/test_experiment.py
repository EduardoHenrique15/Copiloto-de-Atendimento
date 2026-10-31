import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import norm

from copiloto.ds.experiment.analysis import analyze
from copiloto.ds.experiment.assignment import assign_group
from copiloto.ds.experiment.design import build_design
from copiloto.ds.experiment.power import duration_days, plan, sample_size_per_group
from copiloto.ds.experiment.report import render
from copiloto.ds.experiment.simulate import simulate


def test_sample_size_matches_cohen_h_formula():
    p0, r = 0.6, 0.2
    h = 2 * math.asin(math.sqrt(p0)) - 2 * math.asin(math.sqrt(p0 * (1 - r)))
    # Var(2·arcsen(√p̂)) ≈ 1/n; a diferença de dois grupos tem variância 2/n.
    expected = 2 * ((norm.ppf(0.975) + norm.ppf(0.8)) / h) ** 2
    assert sample_size_per_group(p0, r) == math.ceil(expected)


def test_smaller_effect_needs_more_orders():
    rows = plan(0.6, daily_eligible=10)
    sizes = [r["n_per_group"] for r in rows]
    assert sizes == sorted(sizes, reverse=True)


def test_duration():
    assert duration_days(100, daily_eligible=20) == 10
    with pytest.raises(ValueError):
        duration_days(100, 0)


def test_invalid_rates_rejected():
    with pytest.raises(ValueError):
        sample_size_per_group(1.2, 0.1)


def test_assignment_is_deterministic_and_balanced():
    ids = [f"pedido-{i}" for i in range(20000)]
    first = [assign_group(i, 42) for i in ids]
    assert first == [assign_group(i, 42) for i in ids]
    share = np.mean([g == "treatment" for g in first])
    assert abs(share - 0.5) < 0.01


def test_new_seed_gives_independent_assignment():
    ids = [f"pedido-{i}" for i in range(5000)]
    a = np.array([assign_group(i, 1) == "treatment" for i in ids])
    b = np.array([assign_group(i, 2) == "treatment" for i in ids])
    assert 0.45 < np.mean(a == b) < 0.55


def test_analyze_by_hand():
    r = analyze(np.array([1] * 30 + [0] * 70), np.array([1] * 50 + [0] * 50))
    assert r["diff"] == pytest.approx(-0.2)
    assert r["relative_change"] == pytest.approx(-0.4)
    assert r["significant"]
    assert r["ci_low"] < -0.2 < r["ci_high"]


def test_simulation_controls_false_positives_and_detects_large_effect():
    rng = np.random.default_rng(0)
    ids = [f"o{i}" for i in range(3000)]
    y = (rng.random(3000) < 0.6).astype(int)
    null = simulate(ids, y, effect=0.0, n_sims=200, seed=1)
    big = simulate(ids, y, effect=0.3, n_sims=50, seed=1)
    assert null["share_significant"] < 0.1
    assert null["ci_coverage"] > 0.9
    assert big["share_significant"] > 0.95
    assert big["mean_estimated_relative_change"] == pytest.approx(-0.3, abs=0.05)


def test_build_design_and_render():
    rng = np.random.default_rng(0)
    n = 800
    pool = pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(n)],
            "feature_cutoff_at": pd.Timestamp("2018-05-01")
            + pd.to_timedelta(rng.integers(0, 100, n), unit="D"),
            "is_negative": rng.random(n) < 0.6,
            "probability": rng.uniform(0.4, 0.9, n),
        }
    )
    design = build_design(pool, seed=42, effects=(0.0, 0.2), n_sims=20)
    assert design["pool"]["n"] == n
    assert len(design["plan"]) == 3
    md = render(design)
    assert "Pedidos por grupo" in md
