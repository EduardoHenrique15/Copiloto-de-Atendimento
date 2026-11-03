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


def _fmt_pct(value: float | None) -> str:
    return "sem dados" if value is None else f"{value:.0%}".replace(".", ",")


def _fmt_ms(value: float | None) -> str:
    return "sem dados" if value is None else f"{value / 1000:.1f} s".replace(".", ",")


def report_text(m: dict) -> str:
    """Resumo em texto dos indicadores, para o relatório semanal do n8n (sem LLM)."""
    period = "da semana" if m["period"] == "week" else "do dia"
    top = sorted(m["tickets_by_category"].items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    top_text = ", ".join(f"{cat} ({n})" for cat, n in top) or "nenhum ticket"
    cost = f"R$ {m['cost_brl']:.2f}".replace(".", ",")
    return "\n".join(
        [
            f"Relatório {period} do Copiloto de Atendimento",
            f"Tickets triados: {sum(m['tickets_by_category'].values())}. Mais comuns: {top_text}.",
            f"Rascunhos: {m['drafts']}. Bloqueados por guardrail: "
            f"{_fmt_pct(m['guardrail_block_rate'])}.",
            f"Decisões do atendente: {m['feedback']}. Aprovados sem edição: "
            f"{_fmt_pct(m['approval_without_edit_rate'])}.",
            f"Chamadas ao LLM: {m['llm_calls']}. Custo de referência: {cost}. "
            f"Latência p50 {_fmt_ms(m['latency_p50_ms'])}, p95 {_fmt_ms(m['latency_p95_ms'])}.",
        ]
    )


def check_alerts(
    m: dict, max_cost_brl: float, max_p95_ms: float, max_guardrail_rate: float
) -> list[dict]:
    """Limites da seção 10.2 (fluxo 4). Mesma regra usada no painel e no n8n."""
    rules = [
        ("custo do dia (R$)", m["cost_brl"], max_cost_brl),
        ("latência p95 (ms)", m["latency_p95_ms"], max_p95_ms),
        ("taxa de bloqueio dos guardrails", m["guardrail_block_rate"], max_guardrail_rate),
    ]
    return [
        {
            "name": name,
            "value": value,
            "limit": limit,
            "breached": value is not None and value > limit,
        }
        for name, value, limit in rules
    ]
