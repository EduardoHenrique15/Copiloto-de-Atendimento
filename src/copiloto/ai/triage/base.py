"""Contrato comum às abordagens de triagem."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TriageResult:
    category: str
    confidence: float
    latency_ms: float
    multiple_problems: bool | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cached: bool = False


class Triager(Protocol):
    """Classifica um texto de reclamação numa categoria da taxonomia."""

    name: str

    def predict(self, text: str) -> TriageResult: ...
