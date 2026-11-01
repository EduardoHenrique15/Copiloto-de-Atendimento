import pandas as pd
import pytest
from sqlalchemy.orm import Session

from copiloto.ai.triage.base import TriageResult
from copiloto.ai.triage.compare import fixed_routing, summarize
from copiloto.ai.triage.fallback import FallbackTriager
from copiloto.core.errors import ExternalServiceError
from copiloto.db.models import Base
from copiloto.db.session import make_engine
from copiloto.services.triage import TriageService


class Fixed:
    def __init__(self, name, result=None, error=None):
        self.name, self.result, self.error, self.calls = name, result, error, 0

    def predict(self, text):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


LLM_OK = TriageResult("outro", 0.97, 900.0, input_tokens=300, output_tokens=20)
LLM_INVALID = TriageResult("outro", 0.0, 900.0, input_tokens=600, output_tokens=40)
LOCAL = TriageResult("produto_errado_ou_incompleto", 0.8, 20.0)


def test_primary_answers_when_it_works():
    backup = Fixed("embeddings_lr", LOCAL)
    result = FallbackTriager(Fixed("zero_shot", LLM_OK), backup).predict("x")
    assert result == LLM_OK and backup.calls == 0


def test_fallback_when_llm_is_unavailable():
    primary = Fixed("zero_shot", error=ExternalServiceError("LLM indisponível"))
    result = FallbackTriager(primary, Fixed("embeddings_lr", LOCAL)).predict("x")
    assert result.category == LOCAL.category and result.fallback_source == "embeddings_lr"


def test_fallback_on_invalid_answer_keeps_spent_tokens():
    result = FallbackTriager(
        Fixed("zero_shot", LLM_INVALID), Fixed("embeddings_lr", LOCAL)
    ).predict("x")
    assert result.fallback_source == "embeddings_lr"
    assert (result.input_tokens, result.output_tokens) == (600, 40)


class NoOrders:
    def get(self, order_id):
        return None


@pytest.mark.parametrize(
    ("primary", "review", "model"),
    [
        (Fixed("zero_shot", TriageResult("outro", 0.9, 1.0)), True, "gemini"),
        (Fixed("zero_shot", error=ExternalServiceError("x")), False, "embeddings_lr"),
    ],
)
def test_service_uses_threshold_of_who_answered(primary, review, model):
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    triager = FallbackTriager(primary, Fixed("embeddings_lr", LOCAL))
    service = TriageService(
        triager, NoOrders(), 0.95, model_name="gemini", fallback_min_confidence=0.75
    )
    with Session(engine) as session:
        ticket, _ = service.triage(session, "t1", "texto", None)
        assert ticket.needs_human_review is review and ticket.model == model


def test_summarize_applies_threshold_from_validation():
    frame = pd.DataFrame(
        {
            "complaint_id": list("abcd"),
            "label": ["outro"] * 4,
            "pred": ["outro", "outro", "sem_problema", "outro"],
            "confidence": [0.96, 0.5, 0.97, 0.2],
            "latency_ms": [1.0] * 4,
            "input_tokens": [0] * 4,
            "output_tokens": [0] * 4,
            "multiple_problems": [False] * 4,
            "text": list("abcd"),
        }
    )
    routing = summarize(frame, fixed_threshold=0.95)["routing"]
    assert routing["threshold"] == 0.95 and routing["from_validation"]
    assert routing["coverage"] == 0.5 and routing["accuracy_auto"] == 0.5
    with pytest.raises(ValueError):
        fixed_routing([{"threshold": 0.5}], 0.42)
