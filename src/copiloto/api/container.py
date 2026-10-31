"""Monta as dependências da API a partir da configuração (ou de dublês, nos testes)."""

from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy.orm import Session, sessionmaker

from copiloto.core.config import Settings
from copiloto.services.drafting import DraftService
from copiloto.services.risk import RiskBatchService
from copiloto.services.triage import TriageService

ROOT = Path(__file__).resolve().parents[3]


@dataclass
class Container:
    sessions: sessionmaker[Session]
    api_key: str
    triage: TriageService
    drafting: DraftService
    risk: RiskBatchService | None = None
    extras: dict = field(default_factory=dict)


def build_container(settings: Settings) -> Container:
    """Dependências reais: banco, LLM, embeddings, ChromaDB e modelos salvos."""
    from copiloto.ai.copilot.policies import load_policies
    from copiloto.ai.copilot.retrieve import PolicyRetriever
    from copiloto.ai.triage import zero_shot
    from copiloto.ai.triage.embeddings_lr import EmbeddingsLRTriager, SentenceTransformerEmbedder
    from copiloto.core.costs import LLMPrice
    from copiloto.core.errors import ConfigurationError
    from copiloto.db.models import Base
    from copiloto.db.session import make_engine, session_factory
    from copiloto.integrations.llm import OpenAICompatibleLLM
    from copiloto.integrations.orders import DuckDBOrders
    from copiloto.integrations.vectorstore import ChromaVectorStore
    from copiloto.services.risk import RiskModel

    if settings.api_key is None:
        raise ConfigurationError("Defina API_KEY no .env.")
    engine = make_engine(settings.database_url)
    if settings.database_url.startswith("sqlite"):
        Base.metadata.create_all(engine)  # PostgreSQL usa as migrações (alembic upgrade head)
    price = LLMPrice.from_settings(settings) if settings.usd_brl else None
    llm = OpenAICompatibleLLM.from_settings(settings)
    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    orders = DuckDBOrders(settings.duckdb_path)

    if settings.triage_backend == "zero_shot":
        triager, prompt_version = zero_shot.ZeroShotTriager(llm), zero_shot.PROMPT_VERSION
    elif settings.triage_backend == "embeddings_lr":
        path = ROOT / "models" / "triage" / "embeddings_lr.joblib"
        triager, prompt_version = EmbeddingsLRTriager.load(path, embedder), ""
    else:
        raise ConfigurationError("TRIAGE_BACKEND bertimbau ainda não é servido pela API.")

    retriever = PolicyRetriever(
        load_policies(ROOT / "policies"), embedder, ChromaVectorStore(settings.chroma_dir)
    )
    if retriever.store.count() == 0:
        retriever.index()
    risk_path = ROOT / "models" / "risk" / "risk_model.joblib"
    risk = (
        RiskBatchService(
            RiskModel.load(risk_path), orders, settings.ab_seed, settings.proactive_max_per_day
        )
        if risk_path.exists()
        else None
    )
    return Container(
        sessions=session_factory(engine),
        api_key=settings.api_key.get_secret_value(),
        triage=TriageService(
            triager,
            orders,
            settings.triage_min_confidence,
            price,
            model_name=settings.llm_model
            if settings.triage_backend == "zero_shot"
            else "embeddings_lr",
            prompt_version=prompt_version,
        ),
        drafting=DraftService(llm, retriever, orders, settings.rag_top_k, price),
        risk=risk,
    )
