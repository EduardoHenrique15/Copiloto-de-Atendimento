"""Geração do rascunho de resposta com RAG e guardrails antes e depois do LLM."""

import json
import time
from dataclasses import dataclass, field

from pydantic import BaseModel, ValidationError, field_validator

from copiloto.ai.copilot.policies import ACTIONS, PolicyChunk
from copiloto.ai.copilot.prompt import PROMPT_VERSION, build_messages
from copiloto.ai.copilot.retrieve import PolicyRetriever
from copiloto.ai.guardrails import GuardrailEvent
from copiloto.ai.guardrails.injection import detect_injection
from copiloto.ai.guardrails.output_check import check_promises, check_style
from copiloto.ai.guardrails.pii import mask_pii
from copiloto.ai.guardrails.policy import check_action, check_citations
from copiloto.core.logging import get_logger
from copiloto.integrations.llm import LLMClient

log = get_logger("copilot")

FALLBACK_RESPONSE = (
    "Olá! Recebemos a sua mensagem e sentimos muito pelo transtorno. O seu caso foi "
    "encaminhado para um especialista, que vai entrar em contato com você."
)


class DraftOutput(BaseModel):
    resposta: str
    politicas_citadas: list[str] = []
    acao_sugerida: str = "escalar"
    precisa_humano: bool = True
    motivo: str = ""

    @field_validator("acao_sugerida")
    @classmethod
    def known_action(cls, value: str) -> str:
        if value not in ACTIONS:
            raise ValueError(f"ação desconhecida: {value}")
        return value


@dataclass
class DraftResult:
    response: str
    policies_cited: list[str]
    suggested_action: str
    needs_human: bool
    reason: str
    guardrail_flags: list[str]
    events: list[GuardrailEvent] = field(default_factory=list)
    retrieved: list[str] = field(default_factory=list)
    prompt_version: str = PROMPT_VERSION
    model: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: float = 0.0


def _order_sources(order: dict) -> list[str]:
    """Dados do pedido em texto, para o guardrail de promessas aceitar valores reais."""
    parts = []
    if order.get("delay_days") is not None:
        parts.append(f"{abs(round(order['delay_days']))} dias")
    if order.get("items_price") is not None:
        parts.append(f"R$ {order['items_price']:.2f}".replace(".", ","))
    return parts


def generate_draft(
    llm: LLMClient,
    retriever: PolicyRetriever,
    complaint: str,
    category: str | None,
    order: dict,
    k: int = 4,
) -> DraftResult:
    """1. mascara dados pessoais; 2. detecta injection; 3. recupera políticas;
    4. chama o LLM; 5. aplica os guardrails de saída; 6. decide se precisa de humano."""
    start = time.perf_counter()
    masked, events = mask_pii(complaint)
    events += detect_injection(masked)
    policies: list[PolicyChunk] = retriever.retrieve(masked, category, k)
    messages = build_messages(masked, category, order, policies)

    output, tokens_in, tokens_out, model = None, 0, 0, ""
    for attempt in range(2):
        if attempt:
            messages = [*messages, {"role": "user", "content": "JSON inválido. Responda de novo."}]
        response = llm.complete(messages, json_mode=True)
        tokens_in += response.input_tokens
        tokens_out += response.output_tokens
        model = response.model
        try:
            output = DraftOutput.model_validate(json.loads(response.content))
            break
        except (json.JSONDecodeError, ValidationError):
            continue
    if output is None:
        events.append(GuardrailEvent("invalid_output", "rascunho padrão de encaminhamento"))
        output = DraftOutput(resposta=FALLBACK_RESPONSE, motivo="Saída inválida do LLM.")

    text, pii_out = mask_pii(output.resposta)
    events += [GuardrailEvent("pii_in_output", e.detail) for e in pii_out]
    cited, citation_events = check_citations(output.politicas_citadas, policies)
    action, action_events = check_action(output.acao_sugerida, cited, policies)
    events += citation_events + action_events
    events += check_promises(text, [p.text for p in policies] + _order_sources(order))
    events += check_style(text)

    flags = sorted({e.type for e in events})
    blocking = {
        "prompt_injection",
        "unsupported_promise",
        "forbidden_terms",
        "too_long",
        "empty_response",
        "invalid_output",
        "missing_citation",
        "action_not_allowed",
    }
    if any(e.type == "unsupported_promise" for e in events):
        text = FALLBACK_RESPONSE
        action = "escalar"
    needs_human = output.precisa_humano or action == "escalar" or bool(blocking & set(flags))
    for event in events:
        log.info("guardrail_triggered", type=event.type, detail=event.detail)

    return DraftResult(
        response=text,
        policies_cited=cited,
        suggested_action=action,
        needs_human=needs_human,
        reason=output.motivo,
        guardrail_flags=flags,
        events=events,
        retrieved=[p.id for p in policies],
        model=model,
        input_tokens=tokens_in,
        output_tokens=tokens_out,
        latency_ms=(time.perf_counter() - start) * 1000,
    )
