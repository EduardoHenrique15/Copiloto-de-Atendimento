"""Guardrail 1: dados pessoais (CPF, e-mail, telefone e CEP)."""

import re

from copiloto.ai.guardrails import GuardrailEvent

# A ordem importa: CPF antes de telefone, para 11 dígitos seguidos virarem CPF.
PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("email", re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")),
    ("cpf", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b")),
    ("telefone", re.compile(r"(?:\(?\b\d{2}\)?[\s-]?)?\b9?\d{4}[\s-]?\d{4}\b")),
    ("cep", re.compile(r"\b\d{5}-\d{3}\b")),
)


def mask_pii(text: str) -> tuple[str, list[GuardrailEvent]]:
    """Troca cada dado pessoal por um marcador, como [CPF], e conta o que foi trocado."""
    events = []
    for kind, pattern in PATTERNS:
        text, n = pattern.subn(f"[{kind.upper()}]", text)
        if n:
            events.append(GuardrailEvent("pii_masked", f"{kind}: {n}"))
    return text, events
