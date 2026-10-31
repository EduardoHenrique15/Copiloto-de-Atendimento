"""Logs estruturados em JSON, com correlation id."""

import logging
import sys
import uuid

import structlog


def configure_logging(level: str = "INFO") -> None:
    """Configura o structlog para emitir uma linha JSON por evento."""
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level, force=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(ensure_ascii=False),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.getLevelName(level)),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Devolve um logger; `name` vira o campo `logger` de cada evento."""
    logger = structlog.get_logger()
    return logger.bind(logger=name) if name else logger


def bind_correlation_id(correlation_id: str | None = None) -> str:
    """Associa um correlation id a todos os logs do contexto atual e o devolve."""
    cid = correlation_id or uuid.uuid4().hex
    structlog.contextvars.bind_contextvars(correlation_id=cid)
    return cid


def clear_correlation_id() -> None:
    """Remove o correlation id do contexto atual."""
    structlog.contextvars.unbind_contextvars("correlation_id")
