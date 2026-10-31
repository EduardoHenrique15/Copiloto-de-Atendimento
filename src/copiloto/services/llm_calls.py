"""Registro de cada chamada ao LLM na tabela llm_calls."""

from sqlalchemy.orm import Session

from copiloto.core.costs import LLMPrice, llm_cost_brl
from copiloto.db.models import LLMCall


def record_llm_call(
    session: Session,
    feature: str,
    model: str,
    prompt_version: str,
    input_tokens: int,
    output_tokens: int,
    latency_ms: float,
    price: LLMPrice | None,
    status: str = "ok",
    correlation_id: str | None = None,
) -> None:
    """Grava uma chamada. Sem preço configurado, o custo fica 0 (plano gratuito)."""
    cost = llm_cost_brl(input_tokens, output_tokens, price) if price else 0.0
    session.add(
        LLMCall(
            feature=feature,
            model=model,
            prompt_version=prompt_version,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_brl=cost,
            latency_ms=latency_ms,
            status=status,
            correlation_id=correlation_id,
        )
    )
