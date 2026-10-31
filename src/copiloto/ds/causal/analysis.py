"""Análise completa: propensão, sobreposição, balanceamento, IPW, pareamento,
bootstrap, sensibilidade e tradução em negócio."""

import numpy as np
import pandas as pd

from copiloto.ds.causal.balance import balance_summary, balance_table
from copiloto.ds.causal.data import SCORE, as_arrays, design_matrix
from copiloto.ds.causal.estimators import (
    ipw_effect,
    ipw_weights,
    match_att,
    naive_difference,
)
from copiloto.ds.causal.propensity import fit_propensity, overlap_summary
from copiloto.ds.causal.sensitivity import e_value, e_value_for_ci

SEED = 42


def _estimate(x: pd.DataFrame, t: np.ndarray, y: np.ndarray) -> dict[str, float]:
    e = fit_propensity(x, t)
    ipw = ipw_effect(e, t, y, "att")
    m = match_att(e, t, y)
    return {
        "naive": naive_difference(t, y),
        "ipw_att": ipw["effect"],
        "ipw_att_control_mean": ipw["mean_control"],
        "ipw_ate": ipw_effect(e, t, y, "ate")["effect"],
        "matching_att": m["effect"],
    }


def bootstrap(
    x: pd.DataFrame, t: np.ndarray, y: np.ndarray, n_boot: int = 200, seed: int = SEED
) -> dict[str, dict[str, float]]:
    """IC 95% por bootstrap. A propensão é reajustada em cada reamostra, para
    incluir a incerteza do próprio modelo de propensão."""
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(t), len(t))
        draws.append(_estimate(x.iloc[idx], t[idx], y[idx]))
    frame = pd.DataFrame(draws)
    return {
        col: {
            "ci_low": float(frame[col].quantile(0.025)),
            "ci_high": float(frame[col].quantile(0.975)),
            "se": float(frame[col].std()),
        }
        for col in frame.columns
    }


def run_causal(df: pd.DataFrame, n_boot: int = 200, negative_review_cost_brl: float = 30.0) -> dict:
    """Roda a análise e devolve um relatório serializável."""
    x = design_matrix(df)
    t, y = as_arrays(df)
    score = df[SCORE].to_numpy(dtype=float)

    e = fit_propensity(x, t)
    w_att = ipw_weights(e, t, "att")
    ipw = ipw_effect(e, t, y, "att")
    ipw_score = ipw_effect(e, t, score, "att")
    matched = match_att(e, t, y)
    matched_score = match_att(e, t, score)
    table = balance_table(
        x, t, w_att, (matched["matched_treated_idx"], matched["matched_control_idx"])
    )

    point = {
        "naive": naive_difference(t, y),
        "ipw_att": ipw["effect"],
        "ipw_att_control_mean": ipw["mean_control"],
        "ipw_ate": ipw_effect(e, t, y, "ate")["effect"],
        "matching_att": matched["effect"],
    }
    ci = bootstrap(x, t, y, n_boot=n_boot)

    # Razão de risco do ATT: taxa negativa dos atrasados / taxa que teriam sem atraso.
    rr = ipw["mean_treated"] / ipw["mean_control"]
    rr_low = ipw["mean_treated"] / (ipw["mean_treated"] - ci["ipw_att"]["ci_low"])
    per_1000 = 1000 * point["ipw_att"]

    return {
        "n_orders": len(t),
        "n_late": int(t.sum()),
        "late_rate": float(t.mean()),
        "negative_rate_late": float(y[t == 1].mean()),
        "negative_rate_on_time": float(y[t == 0].mean()),
        "n_covariates": x.shape[1],
        "overlap": overlap_summary(e, t),
        "balance": balance_summary(table),
        "balance_table": {
            col: {k: float(v) for k, v in row.items()} for col, row in table.iterrows()
        },
        "estimates": point,
        "bootstrap": {**ci, "n_boot": n_boot},
        "matching_details": {k: v for k, v in matched.items() if not k.endswith("_idx")},
        "score_effect": {
            "naive": naive_difference(t, score),
            "ipw_att": ipw_score["effect"],
            "matching_att": matched_score["effect"],
        },
        "sensitivity": {
            "risk_ratio": rr,
            "risk_ratio_ci_low": rr_low,
            "e_value": e_value(rr),
            "e_value_ci": e_value_for_ci(rr_low),
        },
        "business": {
            "extra_negatives_per_1000_late": per_1000,
            "extra_negatives_per_1000_late_ci": [
                1000 * ci["ipw_att"]["ci_low"],
                1000 * ci["ipw_att"]["ci_high"],
            ],
            "negative_review_cost_brl": negative_review_cost_brl,
            "cost_per_1000_late_brl": per_1000 * negative_review_cost_brl,
            "late_orders_in_base": int(t.sum()),
            "extra_negatives_in_base": float(point["ipw_att"] * t.sum()),
        },
        "propensity": e,
        "treatment": t,
    }
