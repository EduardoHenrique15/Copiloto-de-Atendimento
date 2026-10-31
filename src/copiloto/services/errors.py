"""Erros de caso de uso, traduzidos em códigos HTTP pela API."""

from copiloto.core.errors import CopilotoError


class NotFoundError(CopilotoError):
    """Recurso inexistente (404)."""


class ConflictError(CopilotoError):
    """Operação incompatível com o estado atual (409)."""
