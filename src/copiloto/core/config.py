"""Configuração do projeto, lida do ambiente e do arquivo .env."""

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from copiloto.core.errors import ConfigurationError


class Settings(BaseSettings):
    """Todas as variáveis do `.env.example`, validadas na inicialização.

    Segredos usam `SecretStr` para não aparecerem em logs nem em `repr`.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Geral
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    tz: str = "America/Recife"
    api_key: SecretStr | None = None

    # Banco
    database_url: str = "sqlite:///./copiloto.db"

    # Dados
    data_dir: Path = Path("./data")

    # LLM
    llm_base_url: str | None = None
    llm_api_key: SecretStr | None = None
    llm_model: str | None = None
    llm_temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    llm_cache_dir: Path = Path("./.llm_cache")
    llm_price_input_usd_per_mtok: float = Field(default=0.0, ge=0.0)
    llm_price_output_usd_per_mtok: float = Field(default=0.0, ge=0.0)
    llm_price_quote_date: date | None = None
    usd_brl: float | None = Field(default=None, gt=0.0)

    # Embeddings e RAG
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    chroma_dir: Path = Path("./.chroma")
    rag_top_k: int = Field(default=4, ge=1, le=20)

    # Triagem
    triage_backend: Literal["zero_shot", "embeddings_lr", "bertimbau"] = "embeddings_lr"
    triage_min_confidence: float = Field(default=0.6, ge=0.0, le=1.0)

    # Risco e experimento
    risk_contact_cost_brl: float = Field(default=2.0, ge=0.0)
    risk_negative_review_cost_brl: float = Field(default=30.0, ge=0.0)
    risk_assumed_contact_effect: float = Field(default=0.2, ge=0.0, le=1.0)
    ab_seed: int = 42
    proactive_max_per_day: int = Field(default=20, ge=0)

    # Automação e notificações
    test_email_to: str | None = None
    alert_max_daily_cost_brl: float = Field(default=5.0, ge=0.0)
    alert_max_p95_latency_ms: int = Field(default=5000, ge=0)
    alert_max_guardrail_rate: float = Field(default=0.2, ge=0.0, le=1.0)

    @property
    def raw_dir(self) -> Path:
        """Pasta dos CSVs originais da Olist."""
        return self.data_dir / "raw"

    @property
    def processed_dir(self) -> Path:
        """Pasta das saídas do dbt."""
        return self.data_dir / "processed"

    @property
    def duckdb_path(self) -> Path:
        """Arquivo DuckDB gerado pelo dbt."""
        return self.processed_dir / "copiloto.duckdb"


@lru_cache
def get_settings() -> Settings:
    """Carrega a configuração uma única vez.

    Converte erros de validação em `ConfigurationError` com os nomes das variáveis
    inválidas, sem repetir os valores (que podem ser segredos).
    """
    try:
        return Settings()
    except ValidationError as exc:
        fields = sorted({".".join(str(p) for p in err["loc"]).upper() for err in exc.errors()})
        raise ConfigurationError(f"Variáveis de ambiente inválidas: {', '.join(fields)}") from None
