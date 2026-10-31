"""Balanceamento das covariáveis: diferença média padronizada (SMD)."""

import numpy as np
import pandas as pd

SMD_THRESHOLD = 0.1


def _weighted_mean_var(x: np.ndarray, w: np.ndarray) -> tuple[float, float]:
    mean = np.average(x, weights=w)
    return float(mean), float(np.average((x - mean) ** 2, weights=w))


def smd(x: pd.DataFrame, t: np.ndarray, w: np.ndarray | None = None) -> pd.Series:
    """SMD de cada coluna: (média tratados - média controles) / desvio combinado.

    O desvio usa as variâncias sem peso, para que antes e depois sejam comparáveis.
    |SMD| < 0,1 é o critério usual de bom balanceamento.
    """
    w = np.ones(len(t)) if w is None else w
    out = {}
    for col in x.columns:
        v = x[col].to_numpy(dtype=float)
        m1, _ = _weighted_mean_var(v[t == 1], w[t == 1])
        m0, _ = _weighted_mean_var(v[t == 0], w[t == 0])
        s = np.sqrt((v[t == 1].var() + v[t == 0].var()) / 2)
        out[col] = 0.0 if s == 0 else (m1 - m0) / s
    return pd.Series(out)


def balance_table(
    x: pd.DataFrame, t: np.ndarray, weights: np.ndarray, matched: tuple[np.ndarray, np.ndarray]
) -> pd.DataFrame:
    """SMD antes, depois do IPW e depois do pareamento."""
    mt, mc = matched
    idx = np.concatenate([mt, mc])
    t_m = np.concatenate([np.ones(len(mt), int), np.zeros(len(mc), int)])
    return pd.DataFrame(
        {
            "before": smd(x, t),
            "ipw": smd(x, t, weights),
            "matching": smd(x.iloc[idx].reset_index(drop=True), t_m),
        }
    )


def balance_summary(table: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Maior |SMD| e quantas covariáveis passam do limite, por método."""
    return {
        col: {
            "max_abs_smd": float(table[col].abs().max()),
            "n_above_threshold": int((table[col].abs() > SMD_THRESHOLD).sum()),
            "n_covariates": len(table),
        }
        for col in table.columns
    }
