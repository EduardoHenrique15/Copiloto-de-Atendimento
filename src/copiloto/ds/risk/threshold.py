"""Escolha do limiar de contato proativo pelo valor esperado em reais."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CostAssumptions:
    """Premissas de negócio (configuráveis no .env).

    contact_cost_brl: custo de um contato proativo.
    negative_review_cost_brl: valor de evitar uma avaliação negativa.
    contact_effect: fração das avaliações negativas evitadas pelo contato.
    """

    contact_cost_brl: float
    negative_review_cost_brl: float
    contact_effect: float

    def breakeven_probability(self) -> float:
        """Probabilidade a partir da qual contatar compensa, se ela estiver calibrada:
        p x efeito x valor > custo do contato."""
        return self.contact_cost_brl / (self.contact_effect * self.negative_review_cost_brl)


def value_at_threshold(
    y: np.ndarray, p: np.ndarray, threshold: float, a: CostAssumptions
) -> dict[str, float]:
    """Valor líquido de contatar todos com probabilidade >= limiar, usando o rótulo real."""
    y, p = np.asarray(y, dtype=bool), np.asarray(p, dtype=float)
    flagged = p >= threshold
    contacts = int(flagged.sum())
    negatives_reached = int((flagged & y).sum())
    avoided = a.contact_effect * negatives_reached
    value = avoided * a.negative_review_cost_brl - contacts * a.contact_cost_brl
    return {
        "threshold": float(threshold),
        "contacts": contacts,
        "negatives_reached": negatives_reached,
        "negatives_avoided": float(avoided),
        "value_brl": float(value),
        "precision": negatives_reached / contacts if contacts else 0.0,
        "recall": negatives_reached / int(y.sum()) if y.any() else 0.0,
    }


def value_curve(
    y: np.ndarray, p: np.ndarray, a: CostAssumptions, thresholds: np.ndarray | None = None
) -> list[dict[str, float]]:
    """Valor para cada limiar da grade (padrão: 0,01 a 0,99)."""
    grid = np.round(np.arange(0.01, 1.0, 0.01), 2) if thresholds is None else thresholds
    return [value_at_threshold(y, p, t, a) for t in grid]


def best_threshold(y: np.ndarray, p: np.ndarray, a: CostAssumptions) -> dict[str, float]:
    """Limiar de maior valor. Empate: o maior limiar (menos contatos)."""
    curve = value_curve(y, p, a)
    return max(curve, key=lambda r: (r["value_brl"], r["threshold"]))


def sensitivity(
    y: np.ndarray,
    p: np.ndarray,
    contact_costs: list[float],
    negative_costs: list[float],
    effects: list[float],
) -> list[dict[str, float]]:
    """Melhor limiar e valor para cada combinação de premissas."""
    rows = []
    for c in contact_costs:
        for v in negative_costs:
            for e in effects:
                a = CostAssumptions(c, v, e)
                best = best_threshold(y, p, a)
                rows.append(
                    {
                        "contact_cost_brl": c,
                        "negative_review_cost_brl": v,
                        "contact_effect": e,
                        "breakeven": a.breakeven_probability(),
                        **best,
                    }
                )
    return rows
