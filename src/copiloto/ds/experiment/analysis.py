"""Análise planejada do teste: comparação de duas proporções."""

import numpy as np
from statsmodels.stats.proportion import confint_proportions_2indep, proportions_ztest


def analyze(y_treatment: np.ndarray, y_control: np.ndarray, alpha: float = 0.05) -> dict:
    """Diferença na taxa negativa (tratamento - controle), IC e valor-p bilateral."""
    y_t, y_c = np.asarray(y_treatment, dtype=int), np.asarray(y_control, dtype=int)
    count = np.array([y_t.sum(), y_c.sum()])
    nobs = np.array([len(y_t), len(y_c)])
    _, p_value = proportions_ztest(count, nobs)
    low, high = confint_proportions_2indep(
        count[0], nobs[0], count[1], nobs[1], method="wald", alpha=alpha
    )
    rate_t, rate_c = count / nobs
    return {
        "n_treatment": int(nobs[0]),
        "n_control": int(nobs[1]),
        "rate_treatment": float(rate_t),
        "rate_control": float(rate_c),
        "diff": float(rate_t - rate_c),
        "relative_change": float((rate_t - rate_c) / rate_c) if rate_c else float("nan"),
        "ci_low": float(low),
        "ci_high": float(high),
        "p_value": float(p_value),
        "significant": bool(p_value < alpha),
    }
