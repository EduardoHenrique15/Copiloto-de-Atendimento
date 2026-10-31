"""Contratos da API. Os testes de contrato (tests/contract) garantem que não mudem sem querer."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Category = Literal[
    "atraso_entrega",
    "nao_recebido",
    "produto_errado_ou_incompleto",
    "produto_defeituoso_ou_qualidade",
    "diferente_do_anuncio",
    "atendimento_vendedor",
    "cancelamento_ou_cobranca",
    "outro",
    "sem_problema",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TriageRequest(Strict):
    ticket_id: str = Field(min_length=1, max_length=64)
    text: str = Field(min_length=1, max_length=5000)
    order_id: str | None = Field(default=None, max_length=64)


class TriageResponse(Strict):
    ticket_id: str
    category: Category
    urgency: Literal["alta", "media", "baixa"]
    confidence: float = Field(ge=0, le=1)
    needs_human_review: bool
    model: str


class DraftRequest(Strict):
    ticket_id: str = Field(min_length=1, max_length=64)


class DraftResponse(Strict):
    draft_id: str
    ticket_id: str
    response: str
    policies_cited: list[str]
    suggested_action: Literal["nenhuma", "cupom", "troca", "reembolso", "escalar"]
    needs_human: bool
    guardrail_flags: list[str]


class FeedbackRequest(Strict):
    draft_id: str = Field(min_length=1, max_length=64)
    decision: Literal["approved", "edited", "rejected"]
    final_text: str | None = Field(default=None, max_length=5000)
    reviewer: str = Field(min_length=1, max_length=64)


class FeedbackResponse(Strict):
    draft_id: str
    decision: Literal["approved", "edited", "rejected"]
    status: str


class RiskBatchRequest(Strict):
    date: date


class RiskReason(Strict):
    feature: str
    value: str | float | int | bool | None
    direction: Literal["aumenta", "reduz"]


class RiskOrder(Strict):
    order_id: str
    probability: float = Field(ge=0, le=1)
    group: Literal["treatment", "control"]
    reasons: list[RiskReason]


class RiskBatchResponse(Strict):
    date: date
    threshold: float
    orders: list[RiskOrder]


class MetricsResponse(Strict):
    period: Literal["day", "week"]
    since: str
    llm_calls: int
    cost_brl: float
    latency_p50_ms: float | None
    latency_p95_ms: float | None
    drafts: int
    guardrail_block_rate: float | None
    feedback: int
    approval_without_edit_rate: float | None
    tickets_by_category: dict[str, int]


class HealthResponse(Strict):
    status: Literal["ok", "degradado"]
    database: Literal["ok", "erro"]


class ErrorResponse(Strict):
    detail: str
