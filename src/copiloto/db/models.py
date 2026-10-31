"""Tabelas do banco operacional (PostgreSQL em produção, SQLite nos testes)."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _now() -> datetime:
    return datetime.now(UTC)


def _uuid() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class Ticket(Base):
    """Reclamação triada. O texto é guardado já com os dados pessoais mascarados."""

    __tablename__ = "tickets"

    ticket_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    order_id: Mapped[str | None] = mapped_column(String(64))
    text_masked: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True)
    urgency: Mapped[str] = mapped_column(String(16))
    confidence: Mapped[float] = mapped_column(Float)
    needs_human_review: Mapped[bool] = mapped_column(Boolean)
    model: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class Draft(Base):
    __tablename__ = "drafts"

    draft_id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), unique=True)
    response: Mapped[str] = mapped_column(Text)
    policies_cited: Mapped[list] = mapped_column(JSON, default=list)
    suggested_action: Mapped[str] = mapped_column(String(16))
    needs_human: Mapped[bool] = mapped_column(Boolean)
    reason: Mapped[str] = mapped_column(Text, default="")
    guardrail_flags: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), default="pendente_aprovacao")
    prompt_version: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.draft_id"), unique=True)
    decision: Mapped[str] = mapped_column(String(16))
    final_text: Mapped[str | None] = mapped_column(Text)
    reviewer: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class LLMCall(Base):
    """Uma linha por chamada ao LLM: custo, tokens e latência (seção 8.6)."""

    __tablename__ = "llm_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    feature: Mapped[str] = mapped_column(String(16), index=True)
    model: Mapped[str] = mapped_column(String(64))
    prompt_version: Mapped[str] = mapped_column(String(32))
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    cost_brl: Mapped[float] = mapped_column(Float)
    latency_ms: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16))
    correlation_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)


class GuardrailEventRow(Base):
    """Evento `guardrail_triggered`. Sem o texto do cliente."""

    __tablename__ = "guardrail_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    draft_id: Mapped[str] = mapped_column(ForeignKey("drafts.draft_id"), index=True)
    type: Mapped[str] = mapped_column(String(32), index=True)
    detail: Mapped[str] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class ABAssignment(Base):
    """Grupo do teste A/B de cada pedido de alto risco (tratamento ou controle)."""

    __tablename__ = "ab_assignments"

    order_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    group: Mapped[str] = mapped_column(String(16))
    probability: Mapped[float] = mapped_column(Float)
    batch_date: Mapped[str] = mapped_column(String(10), index=True)
    seed: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
