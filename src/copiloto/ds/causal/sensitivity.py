"""Sensibilidade a confundidores não observados: E-value (VanderWeele e Ding, 2017)."""

import math


def e_value(risk_ratio: float) -> float:
    """Força mínima (em razão de risco) que um confundidor não observado precisaria
    ter, com o tratamento e com o resultado, para anular o efeito observado."""
    rr = risk_ratio if risk_ratio >= 1 else 1 / risk_ratio
    return rr + math.sqrt(rr * (rr - 1))


def e_value_for_ci(ci_low_rr: float) -> float:
    """E-value do limite do intervalo mais próximo de 1 (efeito positivo).
    Se o intervalo cruza 1, o E-value é 1: nenhum confundidor é necessário."""
    return 1.0 if ci_low_rr <= 1 else e_value(ci_low_rr)
