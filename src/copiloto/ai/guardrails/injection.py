"""Guardrail 2: tentativa de prompt injection no texto do cliente.

O texto continua sendo tratado como dado (vai delimitado no prompt). A detecção
só marca o caso para revisão humana e para o log.
"""

import re
import unicodedata

from copiloto.ai.guardrails import GuardrailEvent

PATTERNS = (
    r"ignor\w* (as |todas as |suas |)(instruc|regras|orientac)",
    r"ignore (all |the |)(previous |prior |)instructions",
    r"esquec\w* (as |todas as |suas |)(instruc|regras)",
    r"(voce|tu) agora (e|eh|sera|vai ser)",
    r"a partir de agora,? (voce|responda|aja)",
    r"aja como",
    r"finja (que|ser)",
    r"(revele|mostre|repita|diga|imprima) (?:(?:o|a|os|as|seu|sua|seus|suas) )*"
    r"(prompt|instruc|regras)",
    r"system prompt|prompt do sistema",
    r"you are now",
    r"conceda (um )?(reembolso|cupom|desconto)",
)
_COMPILED = [re.compile(p) for p in PATTERNS]


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def detect_injection(text: str) -> list[GuardrailEvent]:
    """Lista os padrões encontrados (só o índice do padrão, nunca o trecho do cliente)."""
    normalized = _normalize(text)
    return [
        GuardrailEvent("prompt_injection", f"padrao_{i}")
        for i, pattern in enumerate(_COMPILED)
        if pattern.search(normalized)
    ]
