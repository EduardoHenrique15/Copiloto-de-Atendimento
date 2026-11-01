"""Casos de avaliação do copiloto (`eval/copilot_cases.yaml`), validados por Pydantic."""

import random
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from copiloto.ai.copilot.policies import ACTIONS
from copiloto.ai.taxonomy import CATEGORY_KEYS

TAGS = ("injection", "no_policy", "pii")


class Expected(BaseModel):
    policies: list[str]
    actions: list[str] = Field(min_length=1)
    needs_human: bool | None = None

    @field_validator("actions")
    @classmethod
    def known_actions(cls, value: list[str]) -> list[str]:
        unknown = set(value) - set(ACTIONS)
        if unknown:
            raise ValueError(f"ações desconhecidas: {sorted(unknown)}")
        return value


class CopilotCase(BaseModel):
    id: str
    category: str
    tags: list[str] = []
    complaint: str = Field(min_length=1)
    order: dict
    expected: Expected

    @field_validator("category")
    @classmethod
    def known_category(cls, value: str) -> str:
        if value not in CATEGORY_KEYS:
            raise ValueError(f"categoria desconhecida: {value}")
        return value

    @field_validator("tags")
    @classmethod
    def known_tags(cls, value: list[str]) -> list[str]:
        unknown = set(value) - set(TAGS)
        if unknown:
            raise ValueError(f"tags desconhecidas: {sorted(unknown)}")
        return value


def load_cases(path: Path) -> list[CopilotCase]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    cases = [CopilotCase.model_validate(item) for item in raw]
    ids = [c.id for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("ids de casos repetidos")
    return cases


def select_for_human(cases: list[CopilotCase], n: int = 40, seed: int = 11) -> list[str]:
    """Casos que o Eduardo avalia à mão: sorteio fixo, com a mesma proporção de injection."""
    rng = random.Random(seed)
    injection = sorted(c.id for c in cases if "injection" in c.tags)
    others = sorted(c.id for c in cases if "injection" not in c.tags)
    n_inj = round(n * len(injection) / len(cases))
    chosen = rng.sample(injection, n_inj) + rng.sample(others, n - n_inj)
    return sorted(chosen)
