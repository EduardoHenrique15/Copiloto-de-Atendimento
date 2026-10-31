"""Guardrails 4 e 6: promessas sem base, tamanho e termos proibidos."""

import re

from copiloto.ai.guardrails import GuardrailEvent

MAX_CHARS = 1200
FORBIDDEN_TERMS = (
    "garantimos",
    "garanto",
    "com certeza",
    "sem falta",
    "prometo",
    "culpa sua",
    "culpa do cliente",
    "não podemos fazer nada",
)

# Valores que configuram promessa: dinheiro, porcentagem e prazos.
MONEY_RE = re.compile(r"R\$\s?(\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:,\d{1,2})?)")
PERCENT_RE = re.compile(r"(\d+(?:,\d+)?)\s?%")
TIME_RE = re.compile(r"(\d+)\s?(?:dias?|horas?|semanas?|faturas?)", re.IGNORECASE)


def _money(value: str) -> float:
    return float(value.replace(".", "").replace(",", "."))


def extract_promises(text: str) -> dict[str, set[float]]:
    """Números de dinheiro, porcentagem e prazo presentes no texto."""
    return {
        "dinheiro": {_money(v) for v in MONEY_RE.findall(text)},
        "porcentagem": {_money(v) for v in PERCENT_RE.findall(text)},
        "prazo": {float(v) for v in TIME_RE.findall(text)},
    }


def check_promises(response: str, allowed_sources: list[str]) -> list[GuardrailEvent]:
    """Bloqueia valores que não aparecem nas políticas recuperadas nem nos dados do pedido."""
    allowed: dict[str, set[float]] = {"dinheiro": set(), "porcentagem": set(), "prazo": set()}
    for source in allowed_sources:
        for kind, values in extract_promises(source).items():
            allowed[kind] |= values
    events = []
    for kind, values in extract_promises(response).items():
        unsupported = values - allowed[kind]
        if unsupported:
            events.append(GuardrailEvent("unsupported_promise", f"{kind}: {sorted(unsupported)}"))
    return events


def check_style(response: str) -> list[GuardrailEvent]:
    """Limite de tamanho e lista de termos proibidos (política de tom de voz)."""
    events = []
    if len(response) > MAX_CHARS:
        events.append(GuardrailEvent("too_long", f"{len(response)} > {MAX_CHARS}"))
    lowered = response.lower()
    found = [t for t in FORBIDDEN_TERMS if t in lowered]
    if found:
        events.append(GuardrailEvent("forbidden_terms", ", ".join(found)))
    if not response.strip():
        events.append(GuardrailEvent("empty_response", "resposta vazia"))
    return events
