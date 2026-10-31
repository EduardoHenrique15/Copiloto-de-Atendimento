"""Triagem de um ticket: classifica, calcula a urgência e grava (idempotente)."""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from copiloto.ai.guardrails.pii import mask_pii
from copiloto.ai.taxonomy import urgency
from copiloto.ai.triage.base import Triager
from copiloto.core.costs import LLMPrice
from copiloto.db.models import Ticket
from copiloto.integrations.orders import OrderSource
from copiloto.services.llm_calls import record_llm_call


@dataclass
class TriageService:
    triager: Triager
    orders: OrderSource
    min_confidence: float
    price: LLMPrice | None = None
    model_name: str = ""
    prompt_version: str = ""

    def triage(
        self,
        session: Session,
        ticket_id: str,
        text: str,
        order_id: str | None,
        correlation_id: str | None = None,
    ) -> tuple[Ticket, bool]:
        """Devolve (ticket, criado_agora). Se o ticket já existe, devolve o gravado
        sem classificar de novo (sem nova chamada ao LLM)."""
        existing = session.get(Ticket, ticket_id)
        if existing is not None:
            return existing, False
        masked, _ = mask_pii(text)
        result = self.triager.predict(masked)
        order = self.orders.get(order_id) if order_id else None
        ticket = Ticket(
            ticket_id=ticket_id,
            order_id=order_id,
            text_masked=masked,
            category=result.category,
            urgency=urgency(
                result.category,
                masked,
                (order or {}).get("delay_days"),
                (order or {}).get("order_status"),
            ),
            confidence=result.confidence,
            needs_human_review=result.confidence < self.min_confidence,
            model=self.model_name or getattr(self.triager, "name", "desconhecido"),
        )
        session.add(ticket)
        if result.input_tokens or result.output_tokens:
            record_llm_call(
                session,
                "triage",
                self.model_name,
                self.prompt_version,
                result.input_tokens,
                result.output_tokens,
                result.latency_ms,
                self.price,
                correlation_id=correlation_id,
            )
        session.commit()
        return ticket, True
