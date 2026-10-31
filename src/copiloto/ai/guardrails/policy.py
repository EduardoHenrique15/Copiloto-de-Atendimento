"""Guardrails 3 e 5: ação permitida pelas políticas citadas e citação obrigatória."""

from copiloto.ai.copilot.policies import PolicyChunk
from copiloto.ai.guardrails import GuardrailEvent

ALWAYS_ALLOWED = {"nenhuma", "escalar"}


def check_citations(
    cited: list[str], retrieved: list[PolicyChunk]
) -> tuple[list[str], list[GuardrailEvent]]:
    """Mantém só citações de trechos que foram de fato recuperados.

    Citação inventada é removida. Rascunho sem nenhuma citação válida exige humano.
    """
    retrieved_ids = {c.id for c in retrieved}
    valid = [c for c in dict.fromkeys(cited) if c in retrieved_ids]
    events = []
    if len(valid) < len(set(cited)):
        events.append(GuardrailEvent("invalid_citation", f"{len(set(cited)) - len(valid)}"))
    if not valid:
        events.append(GuardrailEvent("missing_citation", "nenhuma política válida citada"))
    return valid, events


def check_action(
    action: str, cited: list[str], retrieved: list[PolicyChunk]
) -> tuple[str, list[GuardrailEvent]]:
    """A ação sugerida precisa estar permitida por alguma política citada; senão, vira escalar."""
    if action in ALWAYS_ALLOWED:
        return action, []
    by_id = {c.id: c for c in retrieved}
    allowed = {a for cid in cited if cid in by_id for a in by_id[cid].actions}
    if action in allowed:
        return action, []
    return "escalar", [GuardrailEvent("action_not_allowed", f"{action} -> escalar")]
