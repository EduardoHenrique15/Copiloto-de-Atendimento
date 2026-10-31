"""Modelo de propensão: probabilidade de atraso dados os confundidores."""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

CLIP = 0.01


def fit_propensity(x: pd.DataFrame, t: np.ndarray) -> np.ndarray:
    """Ajusta uma regressão logística e devolve P(atraso | X) para cada pedido.

    As probabilidades são limitadas a [0,01; 0,99] para evitar pesos explosivos.
    """
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, C=1.0))
    model.fit(x.to_numpy(), t)
    return np.clip(model.predict_proba(x.to_numpy())[:, 1], CLIP, 1 - CLIP)


def overlap_summary(e: np.ndarray, t: np.ndarray) -> dict[str, float]:
    """Resumo da sobreposição: faixas de propensão de cada grupo e quantos ficam
    fora da faixa comum."""
    e_t, e_c = e[t == 1], e[t == 0]
    low, high = max(e_t.min(), e_c.min()), min(e_t.max(), e_c.max())
    outside = (e < low) | (e > high)
    return {
        "treated_min": float(e_t.min()),
        "treated_max": float(e_t.max()),
        "control_min": float(e_c.min()),
        "control_max": float(e_c.max()),
        "common_low": float(low),
        "common_high": float(high),
        "share_outside_common_support": float(outside.mean()),
        "treated_mean_propensity": float(e_t.mean()),
        "control_mean_propensity": float(e_c.mean()),
        "share_at_clip": float(((e <= CLIP) | (e >= 1 - CLIP)).mean()),
    }
