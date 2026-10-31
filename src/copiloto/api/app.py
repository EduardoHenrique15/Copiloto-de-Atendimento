"""API do Copiloto (FastAPI). Rotas da seção 9 da especificação.

Uso: uvicorn copiloto.api.app:app --host 0.0.0.0 --port 8000
"""

import secrets
from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from copiloto.api import schemas
from copiloto.api.container import Container
from copiloto.core.errors import ConfigurationError, ExternalServiceError
from copiloto.core.logging import bind_correlation_id, clear_correlation_id, get_logger
from copiloto.services.errors import ConflictError, NotFoundError
from copiloto.services.feedback import record_feedback
from copiloto.services.metrics import compute_metrics

log = get_logger("api")
ERRORS = {401: {"model": schemas.ErrorResponse}, 422: {"model": schemas.ErrorResponse}}


def create_app(container: Container) -> FastAPI:
    app = FastAPI(title="Copiloto de Atendimento", version="0.1.0")
    app.state.container = container

    def session() -> Iterator[Session]:
        with container.sessions() as s:
            yield s

    def require_key(x_api_key: Annotated[str | None, Header()] = None) -> None:
        if x_api_key is None or not secrets.compare_digest(x_api_key, container.api_key):
            raise HTTPException(401, "Chave de API ausente ou inválida.")

    Db = Annotated[Session, Depends(session)]  # noqa: N806
    auth = [Depends(require_key)]

    @app.middleware("http")
    async def correlation(request: Request, call_next):  # noqa: ANN001, ANN202
        cid = bind_correlation_id(request.headers.get("x-correlation-id"))
        try:
            response = await call_next(request)
        finally:
            clear_correlation_id()
        response.headers["x-correlation-id"] = cid
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        fields = sorted({".".join(str(p) for p in e["loc"][1:]) for e in exc.errors()})
        return JSONResponse({"detail": f"Entrada inválida: {', '.join(fields)}"}, 422)

    @app.exception_handler(NotFoundError)
    async def not_found(_: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, 404)

    @app.exception_handler(ConflictError)
    async def conflict(_: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, 409)

    @app.exception_handler(ExternalServiceError)
    async def upstream(_: Request, exc: ExternalServiceError) -> JSONResponse:
        log.warning("upstream_error", error=str(exc))
        return JSONResponse({"detail": "Serviço externo indisponível. Tente de novo."}, 503)

    @app.exception_handler(ConfigurationError)
    async def misconfigured(_: Request, exc: ConfigurationError) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, 503)

    @app.exception_handler(Exception)
    async def unexpected(_: Request, exc: Exception) -> JSONResponse:
        log.error("unexpected_error", error_type=type(exc).__name__)
        return JSONResponse({"detail": "Erro interno."}, 500)

    @app.get("/health", response_model=schemas.HealthResponse)
    def health(db: Db) -> schemas.HealthResponse:
        try:
            db.execute(text("select 1"))
            ok = True
        except Exception:  # noqa: BLE001
            ok = False
        return schemas.HealthResponse(
            status="ok" if ok else "degradado", database="ok" if ok else "erro"
        )

    @app.post("/triage", response_model=schemas.TriageResponse, dependencies=auth, responses=ERRORS)
    def triage(body: schemas.TriageRequest, db: Db, request: Request) -> schemas.TriageResponse:
        ticket, _ = container.triage.triage(
            db,
            body.ticket_id,
            body.text,
            body.order_id,
            correlation_id=request.headers.get("x-correlation-id"),
        )
        return schemas.TriageResponse(
            ticket_id=ticket.ticket_id,
            category=ticket.category,
            urgency=ticket.urgency,
            confidence=ticket.confidence,
            needs_human_review=ticket.needs_human_review,
            model=ticket.model,
        )

    @app.post("/draft", response_model=schemas.DraftResponse, dependencies=auth, responses=ERRORS)
    def draft(body: schemas.DraftRequest, db: Db, request: Request) -> schemas.DraftResponse:
        d, _ = container.drafting.draft(
            db, body.ticket_id, correlation_id=request.headers.get("x-correlation-id")
        )
        return schemas.DraftResponse(
            draft_id=d.draft_id,
            ticket_id=d.ticket_id,
            response=d.response,
            policies_cited=d.policies_cited,
            suggested_action=d.suggested_action,
            needs_human=d.needs_human,
            guardrail_flags=d.guardrail_flags,
        )

    @app.post(
        "/feedback", response_model=schemas.FeedbackResponse, dependencies=auth, responses=ERRORS
    )
    def feedback(body: schemas.FeedbackRequest, db: Db) -> schemas.FeedbackResponse:
        fb = record_feedback(db, body.draft_id, body.decision, body.final_text, body.reviewer)
        return schemas.FeedbackResponse(
            draft_id=fb.draft_id,
            decision=fb.decision,
            status={"approved": "aprovado", "edited": "editado", "rejected": "recusado"}[
                fb.decision
            ],
        )

    @app.post(
        "/risk/batch",
        response_model=schemas.RiskBatchResponse,
        dependencies=auth,
        responses=ERRORS,
    )
    def risk_batch(body: schemas.RiskBatchRequest, db: Db) -> schemas.RiskBatchResponse:
        if container.risk is None:
            raise ConfigurationError("Modelo de risco não encontrado. Rode scripts/train_risk.py.")
        orders = container.risk.run(db, body.date)
        return schemas.RiskBatchResponse(
            date=body.date, threshold=container.risk.model.threshold, orders=orders
        )

    @app.get(
        "/metrics", response_model=schemas.MetricsResponse, dependencies=auth, responses=ERRORS
    )
    def metrics(
        db: Db, period: Annotated[str, Query(pattern="^(day|week)$")] = "day"
    ) -> schemas.MetricsResponse:
        return schemas.MetricsResponse(**compute_metrics(db, period))

    return app


def _app_from_settings() -> FastAPI:
    from copiloto.api.container import build_container
    from copiloto.core.config import get_settings
    from copiloto.core.logging import configure_logging

    settings = get_settings()
    configure_logging(settings.log_level)
    return create_app(build_container(settings))


def __getattr__(name: str):  # noqa: ANN202
    """`uvicorn copiloto.api.app:app` monta a app real só quando ela é pedida."""
    if name == "app":
        return _app_from_settings()
    raise AttributeError(name)
