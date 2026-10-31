"""Métricas de classificação e intervalos por bootstrap."""

from collections.abc import Callable

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

from copiloto.ds.risk.calibration import brier, expected_calibration_error

SEED = 42


def classification_metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    """PR-AUC (prioridade, alvo desbalanceado), ROC-AUC, Brier e ECE."""
    y = np.asarray(y, dtype=int)
    return {
        "n": int(len(y)),
        "base_rate": float(y.mean()),
        "pr_auc": float(average_precision_score(y, p)),
        "roc_auc": float(roc_auc_score(y, p)),
        "brier": brier(y, p),
        "ece": expected_calibration_error(y, p),
    }


def bootstrap_diff(
    y: np.ndarray,
    p_a: np.ndarray,
    p_b: np.ndarray,
    metric: Callable[[np.ndarray, np.ndarray], float] = average_precision_score,
    n_boot: int = 500,
    seed: int = SEED,
) -> dict[str, float]:
    """Diferença metric(a) - metric(b) com intervalo de 95% por bootstrap pareado."""
    y, p_a, p_b = np.asarray(y, dtype=int), np.asarray(p_a), np.asarray(p_b)
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            continue
        diffs.append(metric(y[idx], p_a[idx]) - metric(y[idx], p_b[idx]))
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return {
        "diff": float(metric(y, p_a) - metric(y, p_b)),
        "ci_low": float(lo),
        "ci_high": float(hi),
        "n_boot": len(diffs),
    }
