"""Explicações SHAP do LightGBM: global e por pedido."""

import warnings

import numpy as np
import pandas as pd
import shap

from copiloto.ds.risk.models import LightGBMModel


def shap_values(model: LightGBMModel, df: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Contribuição de cada feature (em log-odds) para cada pedido, e o valor base."""
    x = model.transform(df)
    explainer = shap.TreeExplainer(model.model.booster_)
    with warnings.catch_warnings():
        # Aviso informativo do SHAP sobre o formato de saída do LightGBM (tratado abaixo).
        warnings.filterwarnings("ignore", message=".*output has changed to a list.*")
        values = explainer.shap_values(x)
    if isinstance(values, list):  # versões antigas devolvem uma matriz por classe
        values = values[1]
    base = explainer.expected_value
    base = float(base[1] if np.ndim(base) else base)
    return pd.DataFrame(values, columns=x.columns, index=df.index), base


def global_importance(values: pd.DataFrame, top: int = 15) -> list[dict[str, float]]:
    """Média de |SHAP| por feature, da maior para a menor."""
    mean_abs = values.abs().mean().sort_values(ascending=False).head(top)
    return [{"feature": f, "mean_abs_shap": float(v)} for f, v in mean_abs.items()]


def explain_order(
    values: pd.DataFrame, features: pd.DataFrame, row: object, top: int = 5
) -> list[dict[str, object]]:
    """Principais motivos de um pedido: features com maior |SHAP|, com o valor observado."""
    contrib = values.loc[row]
    order = contrib.abs().sort_values(ascending=False).head(top).index
    return [
        {
            "feature": f,
            "value": _plain(features.loc[row, f]),
            "shap": float(contrib[f]),
            "direction": "aumenta" if contrib[f] > 0 else "reduz",
        }
        for f in order
    ]


def _plain(value: object) -> object:
    if isinstance(value, (np.floating, float)):
        return None if np.isnan(value) else round(float(value), 3)
    if isinstance(value, np.integer):
        return int(value)
    return value
