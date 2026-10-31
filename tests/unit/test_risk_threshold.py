import numpy as np
import pytest

from copiloto.ds.risk.threshold import (
    CostAssumptions,
    best_threshold,
    sensitivity,
    value_at_threshold,
)

A = CostAssumptions(contact_cost_brl=2, negative_review_cost_brl=30, contact_effect=0.2)


def test_breakeven_is_cost_over_effect_times_value():
    assert A.breakeven_probability() == pytest.approx(2 / (0.2 * 30))


def test_value_by_hand():
    y = np.array([1, 0, 1, 0])
    p = np.array([0.9, 0.8, 0.2, 0.1])
    r = value_at_threshold(y, p, 0.5, A)
    # 2 contatos, 1 negativa alcançada: 0,2 x 30 x 1 - 2 x 2 = 2.
    assert r["contacts"] == 2
    assert r["negatives_reached"] == 1
    assert r["value_brl"] == pytest.approx(2.0)
    assert r["precision"] == 0.5
    assert r["recall"] == 0.5


def test_nobody_contacted_is_zero():
    assert value_at_threshold(np.array([1, 0]), np.array([0.1, 0.1]), 0.5, A)["value_brl"] == 0


def test_best_threshold_skips_unprofitable_contacts():
    # Calibrado: quem tem p=0,6 é negativo 60% das vezes; p=0,1, 10%.
    y = np.array([1] * 6 + [0] * 4 + [1] * 1 + [0] * 9)
    p = np.array([0.6] * 10 + [0.1] * 10)
    best = best_threshold(y, p, A)
    # Contatar p=0,6 rende 0,2 x 30 x 6 - 2 x 10 = 16; contatar todos rende 0,2 x 30 x 7 - 40 = 2.
    assert 0.1 < best["threshold"] <= 0.6
    assert best["value_brl"] == pytest.approx(16)


def test_sensitivity_has_one_row_per_combination():
    y = np.array([1, 0, 1, 0])
    p = np.array([0.9, 0.8, 0.2, 0.1])
    rows = sensitivity(y, p, [1, 2], [30], [0.1, 0.2, 0.4])
    assert len(rows) == 6
    assert {"breakeven", "threshold", "value_brl"} <= set(rows[0])
