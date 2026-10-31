"""Monta o desenho do A/B a partir do modelo de risco e da base histórica."""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from copiloto.ds.experiment.assignment import assign_group
from copiloto.ds.experiment.power import plan
from copiloto.ds.experiment.simulate import simulate


def score_orders(model_path: Path, df: pd.DataFrame) -> tuple[np.ndarray, float]:
    """Probabilidade calibrada e limiar do modelo de risco salvo na Fase 2."""
    bundle = joblib.load(model_path)
    return bundle["calibrator"].transform(bundle["model"].predict_proba(df)), bundle["threshold"]


def eligible_pool(df: pd.DataFrame, p: np.ndarray, threshold: float, start: str) -> pd.DataFrame:
    """Pedidos de alto risco fora do período de treino do modelo (a partir de `start`)."""
    mask = (p >= threshold) & (df["feature_cutoff_at"] >= pd.Timestamp(start))
    pool = df.loc[mask, ["order_id", "feature_cutoff_at", "is_negative"]].copy()
    pool["probability"] = p[mask]
    return pool


def build_design(
    pool: pd.DataFrame,
    seed: int,
    effects: tuple[float, ...] = (0.0, 0.1, 0.2, 0.3),
    n_sims: int = 500,
) -> dict:
    """Plano de amostra, duração, checagem do sorteio e simulações."""
    days = (pool["feature_cutoff_at"].max() - pool["feature_cutoff_at"].min()).days + 1
    daily = len(pool) / days
    baseline = float(pool["is_negative"].mean())
    ids = pool["order_id"].astype(str).tolist()
    y = pool["is_negative"].to_numpy(dtype=int)
    groups = [assign_group(o, seed) for o in ids]
    return {
        "pool": {
            "n": len(pool),
            "start": str(pool["feature_cutoff_at"].min().date()),
            "end": str(pool["feature_cutoff_at"].max().date()),
            "days": days,
            "daily_eligible": daily,
            "baseline_negative_rate": baseline,
            "mean_probability": float(pool["probability"].mean()),
        },
        "plan": plan(baseline, daily),
        "assignment_check": {
            "seed": seed,
            "share_treatment": float(np.mean([g == "treatment" for g in groups])),
        },
        "simulations": [simulate(ids, y, e, n_sims=n_sims, seed=seed) for e in effects],
    }
