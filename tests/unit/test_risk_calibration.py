import numpy as np
import pytest

from copiloto.ds.risk.calibration import (
    Calibrator,
    brier,
    expected_calibration_error,
    reliability_table,
)


def _calibrated_sample(n=20000, seed=0):
    rng = np.random.default_rng(seed)
    p = rng.uniform(0, 1, n)
    y = (rng.random(n) < p).astype(int)
    return y, p


def test_ece_is_small_for_calibrated_scores():
    y, p = _calibrated_sample()
    assert expected_calibration_error(y, p) < 0.02


def test_isotonic_and_platt_fix_overconfident_scores():
    y, p = _calibrated_sample()
    distorted = p**3  # subestima o risco
    for method in ("isotonic", "platt"):
        fixed = Calibrator(method).fit(distorted, y).transform(distorted)
        assert brier(y, fixed) < brier(y, distorted)
        assert expected_calibration_error(y, fixed) < expected_calibration_error(y, distorted)


def test_none_keeps_scores():
    s = np.array([0.1, 0.5])
    assert np.array_equal(Calibrator("none").fit(s, np.array([0, 1])).transform(s), s)


def test_unknown_method_rejected():
    with pytest.raises(ValueError):
        Calibrator("magica").fit(np.array([0.1]), np.array([0]))


def test_reliability_table_counts_everything():
    y, p = _calibrated_sample(1000)
    rows = reliability_table(y, p, n_bins=10)
    assert sum(r["n"] for r in rows) == 1000
