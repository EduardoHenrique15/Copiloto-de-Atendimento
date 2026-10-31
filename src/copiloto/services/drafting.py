"""Rascunho de resposta para um ticket já triado (idempotente)."""

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from copiloto.ai.copilot.draft import generate_draft
from copiloto.ai.copilot.retrieve import PolicyRetriever
from copiloto.core.costs import LLMPrice
from copiloto.db.models import Draft, GuardrailEventRow, Ticket
from copiloto.integrations.llm import LLMClient
from copiloto.integrations.orders import OrderSource
from copiloto.services.errors import NotFoundError
from copiloto.services.llm_calls import record_llm_call

ORDER_CONTEXT_KEYS = ("order_status", "delay_days", "items_price", "n_items", "main_category")


@dataclass
class DraftService:
    llm: LLMClient
    retriever: PolicyRetriever
    orders: OrderSource
    top_k: int = 4
    price: LLMPrice | None = None

    def draft(
        self, session: Session, ticket_id: str, correlation_id: str | None = None
    ) -> tuple[Draft, bool]:
        ticket = session.get(Ticket, ticket_id)
        if ticket is None:
            raise NotFoundError(f"Ticket {ticket_id} não encontrado. Rode a triagem antes.")
        existing = session.scalar(select(Draft).where(Draft.ticket_id == ticket_id))
        if existing is not None:
            return existing, False
        order = self.orders.get(ticket.order_id) if ticket.order_id else None
        context = {k: (order or {}).get(k) for k in ORDER_CONTEXT_KEYS if order}
        result = generate_draft(
            self.llm, self.retriever, ticket.text_masked, ticket.category, context, self.top_k
        )
        draft = Draft(
            ticket_id=ticket_id,
            response=result.response,
            policies_cited=result.policies_cited,
            suggested_action=result.suggested_action,
            needs_human=result.needs_human,
            reason=result.reason,
            guardrail_flags=result.guardrail_flags,
            prompt_version=result.prompt_version,
        )
        session.add(draft)
        session.flush()
        for event in result.events:
            session.add(
                GuardrailEventRow(
                    draft_id=draft.draft_id, type=event.type, detail=event.detail[:200]
                )
            )
        record_llm_call(
            session,
            "draft",
            result.model,
            result.prompt_version,
            result.input_tokens,
            result.output_tokens,
            result.latency_ms,
            self.price,
            status="fallback" if "invalid_output" in result.guardrail_flags else "ok",
            correlation_id=correlation_id,
        )
        session.commit()
        return draft, True
