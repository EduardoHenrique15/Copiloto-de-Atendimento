"""Guardrails determinísticos aplicados antes e depois do LLM (ADR 0010)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailEvent:
    """Registro de um bloqueio ou correção. Nunca contém o texto do cliente."""

    type: str
    detail: str
