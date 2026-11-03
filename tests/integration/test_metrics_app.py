"""O painel abre com banco vazio, com dados e sem os resultados offline."""

import json
import shutil
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from copiloto.db.models import Base, Ticket
from copiloto.db.session import make_engine, session_factory

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "copiloto" / "dashboard" / "metrics_app.py"

pytestmark = pytest.mark.integration


@pytest.fixture
def env(tmp_path, monkeypatch):
    url = f"sqlite:///{tmp_path / 'painel.db'}"
    Base.metadata.create_all(make_engine(url))
    monkeypatch.setenv("DATABASE_URL", url)
    monkeypatch.chdir(tmp_path)  # sem o .env real
    results = tmp_path / "results"
    results.mkdir()
    monkeypatch.setenv("RESULTS_DIR", str(results))
    import streamlit as st

    from copiloto.core.config import get_settings

    get_settings.cache_clear()
    st.cache_resource.clear()  # o motor do banco fica em cache entre execuções
    yield url, results
    get_settings.cache_clear()


def _texts(at) -> str:
    return " ".join(m.value for m in at.markdown)


def test_empty_panel(env):
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    assert "Nenhum ticket no período" in _texts(at)
    assert "Triagem ainda não avaliada" in _texts(at)


def test_panel_with_tickets_and_results(env):
    url, results = env
    with session_factory(make_engine(url))() as db:
        for i, cat in enumerate(["nao_recebido", "nao_recebido", "outro"]):
            db.add(
                Ticket(
                    ticket_id=f"t{i}",
                    order_id=None,
                    text_masked="x",
                    category=cat,
                    urgency="media",
                    confidence=0.9,
                    needs_human_review=False,
                    model="m",
                )
            )
        db.commit()
    for name in ["triage_comparison_test.json", "copilot_eval.json", "risk_metrics.json"]:
        shutil.copy(ROOT / "eval" / "results" / name, results / name)
    at = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not at.exception
    text = _texts(at)
    assert "Tickets triados" in text and ">3<" in text
    assert "Triagem: acurácia no teste" in text and "83,5%" in text
    assert json.loads((results / "copilot_eval.json").read_text())["n_cases"] == 60
