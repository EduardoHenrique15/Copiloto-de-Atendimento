"""Simulação: aplicar um efeito conhecido nos dados históricos e verificar se a
análise planejada o recupera."""

import numpy as np

from copiloto.ds.experiment.analysis import analyze
from copiloto.ds.experiment.assignment import assign_group


def simulate_once(
    order_ids: list[str], y: np.ndarray, effect: float, seed: int, rng: np.random.Generator
) -> dict:
    """Sorteia os grupos, aplica o efeito no tratamento e analisa.

    O efeito é uma redução relativa: cada avaliação negativa do grupo de
    tratamento vira não negativa com probabilidade `effect`.
    """
    groups = np.array([assign_group(o, seed) for o in order_ids])
    y = np.asarray(y, dtype=int).copy()
    treated = groups == "treatment"
    flip = treated & (y == 1) & (rng.random(len(y)) < effect)
    y[flip] = 0
    return analyze(y[treated], y[~treated])


def simulate(
    order_ids: list[str], y: np.ndarray, effect: float, n_sims: int = 500, seed: int = 0
) -> dict:
    """Repete o experimento com sorteios diferentes.

    Com efeito zero, a taxa de "significativo" estima o falso positivo (~5%).
    Com efeito > 0, estima o poder. A média do efeito estimado mostra se há viés.
    """
    rng = np.random.default_rng(seed)
    results = [simulate_once(order_ids, y, effect, seed + i, rng) for i in range(n_sims)]
    rel = np.array([r["relative_change"] for r in results])
    # Diferença absoluta verdadeira esperada: o efeito relativo vezes a taxa base.
    true_diff = -effect * float(np.mean(y))
    return {
        "true_relative_reduction": effect,
        "true_diff": true_diff,
        "n_sims": n_sims,
        "n_orders": len(order_ids),
        "share_significant": float(np.mean([r["significant"] for r in results])),
        "mean_estimated_relative_change": float(np.nanmean(rel)),
        "ci_coverage": float(np.mean([r["ci_low"] <= true_diff <= r["ci_high"] for r in results])),
    }
