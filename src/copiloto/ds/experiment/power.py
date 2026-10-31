"""Tamanho de amostra e duração do teste."""

import math

from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize

ALPHA = 0.05
POWER = 0.8


def sample_size_per_group(
    baseline_rate: float, relative_reduction: float, alpha: float = ALPHA, power: float = POWER
) -> int:
    """Pedidos por grupo para detectar uma queda relativa na taxa negativa
    (teste bilateral de duas proporções, tamanho de efeito h de Cohen)."""
    if not 0 < baseline_rate < 1 or not 0 < relative_reduction < 1:
        raise ValueError("Taxa e redução precisam estar entre 0 e 1.")
    treated_rate = baseline_rate * (1 - relative_reduction)
    h = abs(proportion_effectsize(baseline_rate, treated_rate))
    n = NormalIndPower().solve_power(effect_size=h, alpha=alpha, power=power, ratio=1.0)
    return math.ceil(n)


def duration_days(n_per_group: int, daily_eligible: float, treatment_share: float = 0.5) -> float:
    """Dias para juntar a amostra, dado o volume diário de pedidos elegíveis."""
    if daily_eligible <= 0:
        raise ValueError("Volume diário precisa ser positivo.")
    per_day_smallest_group = daily_eligible * min(treatment_share, 1 - treatment_share)
    return n_per_group / per_day_smallest_group


def plan(
    baseline_rate: float,
    daily_eligible: float,
    reductions: tuple[float, ...] = (0.1, 0.2, 0.3),
) -> list[dict[str, float]]:
    """Tabela do plano: amostra e duração para cada efeito mínimo detectável."""
    rows = []
    for r in reductions:
        n = sample_size_per_group(baseline_rate, r)
        rows.append(
            {
                "relative_reduction": r,
                "baseline_rate": baseline_rate,
                "treated_rate": baseline_rate * (1 - r),
                "n_per_group": n,
                "n_total": 2 * n,
                "days": duration_days(n, daily_eligible),
            }
        )
    return rows
