"""Concordância entre o juiz LLM e a avaliação humana, critério por critério."""

import math

from sklearn.metrics import cohen_kappa_score

from copiloto.ai.eval.judge import CRITERIA

# Regra definida antes de ver os resultados (ADR 0011).
MIN_AGREEMENT = 0.80
MIN_KAPPA = 0.40


def _kappa(a: list[bool], b: list[bool]) -> float | None:
    if len(set(a) | set(b)) < 2:
        return None  # só uma classe nos dois lados: kappa indefinido
    value = float(cohen_kappa_score(a, b))
    return None if math.isnan(value) else value


def judge_agreement(human: dict[str, dict], judge: dict[str, dict]) -> dict:
    """`human` e `judge`: {case_id: {criterio: bool}}. Usa os casos presentes nos dois."""
    ids = sorted(set(human) & set(judge))
    per = {}
    all_h, all_j = [], []
    for criterion in CRITERIA:
        h = [bool(human[i][criterion]) for i in ids]
        j = [bool(judge[i][criterion]) for i in ids]
        all_h += h
        all_j += j
        per[criterion] = {
            "n": len(ids),
            "agreement": sum(x == y for x, y in zip(h, j, strict=True)) / len(ids) if ids else None,
            "kappa": _kappa(h, j),
            "human_pass_rate": sum(h) / len(ids) if ids else None,
            "judge_pass_rate": sum(j) / len(ids) if ids else None,
        }
    overall = sum(x == y for x, y in zip(all_h, all_j, strict=True)) / len(all_h) if all_h else None
    kappa = _kappa(all_h, all_j)
    acceptable = (
        overall is not None
        and overall >= MIN_AGREEMENT
        and kappa is not None
        and kappa >= MIN_KAPPA
    )
    return {
        "n_cases": len(ids),
        "per_criterion": per,
        "overall_agreement": overall,
        "overall_kappa": kappa,
        "rule": {"min_agreement": MIN_AGREEMENT, "min_kappa": MIN_KAPPA},
        "acceptable": acceptable,
    }
