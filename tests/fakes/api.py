"""Container da API montado só com dublês: SQLite em memória, LLM roteirizado, embeddings falsos."""

from pathlib import Path

import pandas as pd

from copiloto.ai.copilot.policies import load_policies
from copiloto.ai.copilot.retrieve import PolicyRetriever
from copiloto.ai.triage.base import TriageResult
from copiloto.api.container import Container
from copiloto.db.models import Base
from copiloto.db.session import make_engine, session_factory
from copiloto.ds.risk.calibration import Calibrator
from copiloto.ds.risk.models import LightGBMModel
from copiloto.ds.risk.split import temporal_split
from copiloto.integrations.vectorstore import InMemoryVectorStore
from copiloto.services.drafting import DraftService
from copiloto.services.risk import RiskBatchService, RiskModel
from copiloto.services.triage import TriageService
from tests.fakes.embeddings import FakeEmbedder
from tests.fakes.llm import ScriptedLLM
from tests.fakes.risk_data import make_risk_frame

ROOT = Path(__file__).resolve().parents[2]
API_KEY = "chave-de-teste"
KEYWORDS = {
    "não recebi": ("nao_recebido", 0.92),
    "atras": ("atraso_entrega", 0.81),
    "faltando": ("produto_errado_ou_incompleto", 0.88),
}


class KeywordTriager:
    name = "keyword-fake"

    def __init__(self) -> None:
        self.calls = 0

    def predict(self, text: str) -> TriageResult:
        self.calls += 1
        for word, (category, confidence) in KEYWORDS.items():
            if word in text.lower():
                return TriageResult(category, confidence, latency_ms=1.0)
        return TriageResult("outro", 0.4, latency_ms=1.0)


class FakeOrders:
    def __init__(self, delivered: pd.DataFrame) -> None:
        self.orders = {
            "pedido-1": {
                "order_status": "delivered",
                "delay_days": 12.0,
                "items_price": 89.9,
                "n_items": 1,
                "main_category": "bed_bath_table",
            },
        }
        self.delivered = delivered

    def get(self, order_id: str) -> dict | None:
        return self.orders.get(order_id)

    def delivered_on(self, day) -> pd.DataFrame:  # noqa: ANN001
        return self.delivered[self.delivered["feature_cutoff_at"].dt.date == day].copy()


def draft_answer(messages) -> dict:  # noqa: ANN001
    """Responde citando o primeiro trecho de política recebido no prompt."""
    content = messages[1]["content"]
    start = content.find('<politica id="') + len('<politica id="')
    first = content[start : content.find('"', start)]
    return {
        "resposta": "Olá! Sentimos muito pelo ocorrido. Vamos verificar e retornar.",
        "politicas_citadas": [first],
        "acao_sugerida": "nenhuma",
        "precisa_humano": False,
        "motivo": "Teste.",
    }


def make_container(with_risk: bool = True) -> tuple[Container, dict]:
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    frame = make_risk_frame(3000, seed=3)
    orders = FakeOrders(frame)
    retriever = PolicyRetriever(
        load_policies(ROOT / "policies"), FakeEmbedder(), InMemoryVectorStore()
    )
    retriever.index()
    llm = ScriptedLLM(responder=draft_answer)
    triager = KeywordTriager()
    risk = None
    if with_risk:
        split = temporal_split(frame)
        params = {**LightGBMModel().params, "n_estimators": 60}
        model = LightGBMModel(params=params).fit(split.train, split.val)
        bundle = {"model": model, "calibrator": Calibrator("none"), "threshold": 0.3}
        risk = RiskBatchService(RiskModel(bundle), orders, seed=42, max_per_day=3)
    container = Container(
        sessions=session_factory(engine),
        api_key=API_KEY,
        triage=TriageService(triager, orders, min_confidence=0.6, model_name="keyword-fake"),
        drafting=DraftService(llm, retriever, orders, top_k=4),
        risk=risk,
    )
    return container, {"llm": llm, "triager": triager, "frame": frame, "engine": engine}
