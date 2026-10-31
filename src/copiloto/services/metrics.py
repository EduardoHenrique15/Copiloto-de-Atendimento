"""Indicadores da seção 8.6 para o período pedido."""

from datetime import UTC, datetime, timedelta

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from copiloto.db.models import Draft, Feedback, LLMCall, Ticket

PERIODS = {"day": timedelta(days=1), "week": timedelta(days=7)}
BLOCKING_FLAGS = {
    "prompt_injection",
    "unsupported_promise",
    "forbidden_terms",
    "too_long",
    "empty_response",
    "invalid_output",
    "missing_citation",
    "action_not_allowed",
}


def compute_metrics(session: Session, period: str, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    since = now - PERIODS[period]

    calls = session.execute(
        select(LLMCall.cost_brl, LLMCall.latency_ms).where(LLMCall.created_at >= since)
    ).all()
    latencies = np.array([c.latency_ms for c in calls], dtype=float)

    drafts = session.scalars(select(Draft).where(Draft.created_at >= since)).all()
    blocked = sum(1 for d in drafts if BLOCKING_FLAGS & set(d.guardrail_flags or []))

    decisions = dict(
        session.execute(
            select(Feedback.decision, func.count())
            .where(Feedback.created_at >= since)
            .group_by(Feedback.decision)
        ).all()
    )
    total_feedback = sum(decisions.values())

    by_category = dict(
        session.execute(
            select(Ticket.category, func.count())
            .where(Ticket.created_at >= since)
            .group_by(Ticket.category)
        ).all()
    )
    return {
        "period": period,
        "since": since.isoformat(timespec="seconds"),
        "llm_calls": len(calls),
        "cost_brl": round(float(sum(c.cost_brl for c in calls)), 4),
        "latency_p50_ms": float(np.percentile(latencies, 50)) if len(latencies) else None,
        "latency_p95_ms": float(np.percentile(latencies, 95)) if len(latencies) else None,
        "drafts": len(drafts),
        "guardrail_block_rate": blocked / len(drafts) if drafts else None,
        "feedback": total_feedback,
        "approval_without_edit_rate": decisions.get("approved", 0) / total_feedback
        if total_feedback
        else None,
        "tickets_by_category": by_category,
    }
