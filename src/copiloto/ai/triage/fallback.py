"""Triagem com reserva: a abordagem principal responde; se ela falhar, a reserva assume."""

from dataclasses import replace

from copiloto.ai.triage.base import Triager, TriageResult
from copiloto.core.errors import ExternalServiceError


class FallbackTriager:
    """Usa `primary` e, se ela não responder, `fallback` (ADR 0009, decisão de produção).

    Conta como falha: LLM indisponível (`ExternalServiceError`, inclusive cota esgotada)
    ou resposta inválida duas vezes (confiança 0). O resultado da reserva sai com
    `fallback_source` preenchido, para o serviço aplicar o limiar dela.
    """

    def __init__(self, primary: Triager, fallback: Triager) -> None:
        self.primary = primary
        self.fallback = fallback
        self.name = primary.name

    def predict(self, text: str) -> TriageResult:
        try:
            result = self.primary.predict(text)
        except ExternalServiceError:
            result = None
        if result is not None and result.confidence > 0:
            return result
        backup = self.fallback.predict(text)
        if result is not None:  # tokens gastos na tentativa inválida continuam na conta
            backup = replace(
                backup, input_tokens=result.input_tokens, output_tokens=result.output_tokens
            )
        return replace(backup, fallback_source=self.fallback.name)
