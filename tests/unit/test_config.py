from pathlib import Path

import pytest

from copiloto.core import config
from copiloto.core.config import Settings, get_settings
from copiloto.core.errors import ConfigurationError


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch, tmp_path):
    """Roda cada teste numa pasta vazia, sem o .env real do desenvolvedor."""
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_defaults_without_env_file():
    settings = Settings(_env_file=None)
    assert settings.triage_backend == "embeddings_lr"
    assert settings.rag_top_k == 4
    assert settings.data_dir == Path("./data")


def test_derived_paths(monkeypatch):
    monkeypatch.setenv("DATA_DIR", "/tmp/dados")
    settings = Settings(_env_file=None)
    assert settings.raw_dir == Path("/tmp/dados/raw")
    assert settings.duckdb_path == Path("/tmp/dados/processed/copiloto.duckdb")


def test_secret_is_not_exposed_in_repr(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "segredo-de-teste")
    settings = Settings(_env_file=None)
    assert "segredo-de-teste" not in repr(settings)
    assert settings.llm_api_key.get_secret_value() == "segredo-de-teste"


def test_reads_env_file(tmp_path):
    (tmp_path / ".env").write_text("LLM_MODEL=modelo-x\nRAG_TOP_K=7\n", encoding="utf-8")
    settings = Settings()
    assert settings.llm_model == "modelo-x"
    assert settings.rag_top_k == 7


def test_invalid_value_raises_configuration_error_without_value(monkeypatch):
    monkeypatch.setenv("TRIAGE_MIN_CONFIDENCE", "1.5")
    monkeypatch.setenv("LLM_API_KEY", "nao-deve-aparecer")
    with pytest.raises(ConfigurationError) as exc_info:
        get_settings()
    message = str(exc_info.value)
    assert "TRIAGE_MIN_CONFIDENCE" in message
    assert "nao-deve-aparecer" not in message


def test_get_settings_is_cached():
    assert config.get_settings() is config.get_settings()


def test_empty_values_count_as_unset(tmp_path):
    (tmp_path / ".env").write_text(
        "USD_BRL=\nLLM_PRICE_QUOTE_DATE=\nRAG_TOP_K=\n", encoding="utf-8"
    )
    settings = Settings()
    assert settings.usd_brl is None
    assert settings.llm_price_quote_date is None
    assert settings.rag_top_k == 4
