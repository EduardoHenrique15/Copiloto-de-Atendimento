"""Calibração das probabilidades e métricas de calibração."""

from dataclasses import dataclass

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression

EPS = 1e-6


def brier(y: np.ndarray, p: np.ndarray) -> float:
    """Erro quadrático médio da probabilidade (menor é melhor)."""
    return float(np.mean((np.asarray(p) - np.asarray(y)) ** 2))


def reliability_table(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> list[dict]:
    """Por faixa de probabilidade prevista (quantis): média prevista x taxa observada."""
    y, p = np.asarray(y, dtype=float), np.asarray(p, dtype=float)
    edges = np.unique(np.quantile(p, np.linspace(0, 1, n_bins + 1)))
    idx = np.clip(np.searchsorted(edges, p, side="right") - 1, 0, len(edges) - 2)
    rows = []
    for b in range(len(edges) - 1):
        mask = idx == b
        if mask.any():
            rows.append(
                {
                    "n": int(mask.sum()),
                    "predicted": float(p[mask].mean()),
                    "observed": float(y[mask].mean()),
                }
            )
    return rows


def expected_calibration_error(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> float:
    """Média ponderada de |prevista - observada| nas faixas da tabela de confiabilidade."""
    rows = reliability_table(y, p, n_bins)
    total = sum(r["n"] for r in rows)
    return float(sum(r["n"] * abs(r["predicted"] - r["observed"]) for r in rows) / total)


@dataclass
class Calibrator:
    """Ajusta, na validação, um mapa de score bruto para probabilidade calibrada."""

    method: str  # "none", "isotonic" ou "platt"
    _model: object | None = None

    def fit(self, scores: np.ndarray, y: np.ndarray) -> "Calibrator":
        if self.method == "isotonic":
            self._model = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
            self._model.fit(scores, y)
        elif self.method == "platt":
            self._model = LogisticRegression().fit(_logit(scores)[:, None], y)
        elif self.method != "none":
            raise ValueError(f"Método de calibração desconhecido: {self.method}")
        return self

    def transform(self, scores: np.ndarray) -> np.ndarray:
        if self.method == "isotonic":
            return self._model.predict(scores)
        if self.method == "platt":
            return self._model.predict_proba(_logit(scores)[:, None])[:, 1]
        return np.asarray(scores)


def _logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(p, dtype=float), EPS, 1 - EPS)
    return np.log(p / (1 - p))
