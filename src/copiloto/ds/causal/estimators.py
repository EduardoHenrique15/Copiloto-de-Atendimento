"""Estimadores do efeito do atraso: diferença ingênua, IPW e pareamento.

Estimando principal: ATT, o efeito médio do atraso nos pedidos que atrasaram
("quanto pior ficou a nota desses pedidos por causa do atraso").
"""

import numpy as np
from sklearn.neighbors import NearestNeighbors


def naive_difference(t: np.ndarray, y: np.ndarray) -> float:
    """Diferença simples de médias entre atrasados e não atrasados."""
    return float(y[t == 1].mean() - y[t == 0].mean())


def ipw_weights(e: np.ndarray, t: np.ndarray, estimand: str = "att") -> np.ndarray:
    """Pesos por inverso da propensão.

    ATT: tratados pesam 1; controles pesam e/(1-e), para parecerem com os tratados.
    ATE: tratados pesam 1/e; controles, 1/(1-e).
    """
    if estimand == "att":
        return np.where(t == 1, 1.0, e / (1 - e))
    if estimand == "ate":
        return np.where(t == 1, 1 / e, 1 / (1 - e))
    raise ValueError(f"Estimando desconhecido: {estimand}")


def ipw_effect(e: np.ndarray, t: np.ndarray, y: np.ndarray, estimand: str = "att") -> dict:
    """Efeito por IPW normalizado (Hájek): média ponderada em cada grupo."""
    w = ipw_weights(e, t, estimand)
    mu1 = float(np.average(y[t == 1], weights=w[t == 1]))
    mu0 = float(np.average(y[t == 0], weights=w[t == 0]))
    return {"effect": mu1 - mu0, "mean_treated": mu1, "mean_control": mu0}


def match_att(e: np.ndarray, t: np.ndarray, y: np.ndarray, caliper_sd: float = 0.2) -> dict:
    """Pareamento 1:1 pelo vizinho mais próximo no logit da propensão, com reposição.

    Cada atrasado ganha o controle mais parecido. Pares mais distantes que
    `caliper_sd` desvios-padrão do logit são descartados.
    """
    logit = np.log(e / (1 - e))
    caliper = caliper_sd * logit.std()
    treated, control = np.flatnonzero(t == 1), np.flatnonzero(t == 0)
    nn = NearestNeighbors(n_neighbors=1).fit(logit[control, None])
    dist, idx = nn.kneighbors(logit[treated, None])
    keep = dist[:, 0] <= caliper
    matched_t = treated[keep]
    matched_c = control[idx[keep, 0]]
    return {
        "effect": float(y[matched_t].mean() - y[matched_c].mean()),
        "mean_treated": float(y[matched_t].mean()),
        "mean_control": float(y[matched_c].mean()),
        "n_treated_matched": int(keep.sum()),
        "n_treated_dropped": int((~keep).sum()),
        "n_unique_controls": int(len(np.unique(matched_c))),
        "matched_treated_idx": matched_t,
        "matched_control_idx": matched_c,
    }
