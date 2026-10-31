"""Contratos da API usados pelo n8n: formatos, códigos HTTP, autenticação e idempotência."""

import json
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from copiloto.api.app import create_app
from copiloto.db.models import ABAssignment, LLMCall
from tests.fakes.api import API_KEY, make_container

SNAPSHOT = Path(__file__).with_name("openapi_snapshot.json")
H = {"X-API-Key": API_KEY}


@pytest.fixture(scope="module")
def ctx():
    container, deps = make_container()
    return TestClient(create_app(container)), deps


def test_openapi_contract_did_not_change(ctx):
    """Se este teste falhar, o formato mudou: atualize o n8n e o snapshot juntos
    (python tests/contract/update_snapshot.py)."""
    client, _ = ctx
    schemas = client.get("/openapi.json").json()["components"]["schemas"]
    assert schemas == json.loads(SNAPSHOT.read_text(encoding="utf-8"))


def test_health_needs_no_key(ctx):
    client, _ = ctx
    assert client.get("/health").json() == {"status": "ok", "database": "ok"}


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "errada"}])
def test_protected_routes_require_key(ctx, headers):
    client, _ = ctx
    r = client.post("/triage", json={"ticket_id": "t", "text": "x"}, headers=headers)
    assert r.status_code == 401
    assert r.json() == {"detail": "Chave de API ausente ou inválida."}


def test_triage_contract_and_idempotency(ctx):
    client, deps = ctx
    body = {"ticket_id": "t-1", "text": "Não recebi meu pedido", "order_id": "pedido-1"}
    first = client.post("/triage", json=body, headers=H)
    assert first.status_code == 200
    data = first.json()
    assert set(data) == {
        "ticket_id",
        "category",
        "urgency",
        "confidence",
        "needs_human_review",
        "model",
    }
    assert data["category"] == "nao_recebido"
    assert data["urgency"] == "alta"  # não recebido com status entregue
    assert data["needs_human_review"] is False
    calls = deps["triager"].calls
    again = client.post("/triage", json=body, headers=H)
    assert again.json() == data
    assert deps["triager"].calls == calls  # não classificou de novo


def test_low_confidence_goes_to_human_review(ctx):
    client, _ = ctx
    r = client.post("/triage", json={"ticket_id": "t-low", "text": "texto vago"}, headers=H)
    assert r.json()["needs_human_review"] is True


def test_triage_masks_pii_before_storing(ctx):
    client, deps = ctx
    client.post("/triage", json={"ticket_id": "t-pii", "text": "meu cpf 123.456.789-09"}, headers=H)
    from copiloto.db.models import Ticket

    with deps["engine"].connect() as con:
        stored = con.execute(select(Ticket.text_masked).where(Ticket.ticket_id == "t-pii")).scalar()
    assert "123.456" not in stored and "[CPF]" in stored


def test_draft_contract_idempotency_and_llm_log(ctx):
    client, deps = ctx
    client.post("/triage", json={"ticket_id": "t-d", "text": "chegou com atraso"}, headers=H)
    r = client.post("/draft", json={"ticket_id": "t-d"}, headers=H)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {
        "draft_id",
        "ticket_id",
        "response",
        "policies_cited",
        "suggested_action",
        "needs_human",
        "guardrail_flags",
    }
    assert data["policies_cited"] and data["suggested_action"] == "nenhuma"
    llm_calls = len(deps["llm"].calls)
    assert client.post("/draft", json={"ticket_id": "t-d"}, headers=H).json() == data
    assert len(deps["llm"].calls) == llm_calls
    with deps["engine"].connect() as con:
        assert con.execute(select(func.count()).select_from(LLMCall)).scalar() >= 1


def test_draft_for_unknown_ticket_is_404(ctx):
    client, _ = ctx
    r = client.post("/draft", json={"ticket_id": "nao-existe"}, headers=H)
    assert r.status_code == 404 and "triagem" in r.json()["detail"]


def test_feedback_flow(ctx):
    client, _ = ctx
    client.post("/triage", json={"ticket_id": "t-f", "text": "veio faltando"}, headers=H)
    draft_id = client.post("/draft", json={"ticket_id": "t-f"}, headers=H).json()["draft_id"]
    bad = client.post(
        "/feedback", json={"draft_id": draft_id, "decision": "edited", "reviewer": "ana"}, headers=H
    )
    assert bad.status_code == 409
    ok = client.post(
        "/feedback",
        json={
            "draft_id": draft_id,
            "decision": "edited",
            "final_text": "Novo texto",
            "reviewer": "ana",
        },
        headers=H,
    )
    assert ok.json() == {"draft_id": draft_id, "decision": "edited", "status": "editado"}
    twice = client.post(
        "/feedback",
        json={"draft_id": draft_id, "decision": "approved", "reviewer": "ana"},
        headers=H,
    )
    assert twice.status_code == 409


def test_validation_errors_are_clear_and_without_traceback(ctx):
    client, _ = ctx
    r = client.post("/feedback", json={"draft_id": "x", "decision": "talvez"}, headers=H)
    assert r.status_code == 422
    assert r.json()["detail"].startswith("Entrada inválida")
    assert "Traceback" not in r.text
    extra = client.post("/triage", json={"ticket_id": "a", "text": "b", "campo": 1}, headers=H)
    assert extra.status_code == 422


def test_risk_batch_contract_assignment_and_cap(ctx):
    client, deps = ctx
    frame = deps["frame"]
    day = frame["feature_cutoff_at"].dt.date.value_counts().idxmax()
    r = client.post("/risk/batch", json={"date": day.isoformat()}, headers=H)
    assert r.status_code == 200
    data = r.json()
    assert set(data) == {"date", "threshold", "orders"}
    treated = [o for o in data["orders"] if o["group"] == "treatment"]
    assert len(treated) <= 3
    for o in data["orders"]:
        assert set(o) == {"order_id", "probability", "group", "reasons"}
        assert o["probability"] >= data["threshold"]
    again = client.post("/risk/batch", json={"date": day.isoformat()}, headers=H).json()
    assert [(o["order_id"], o["group"]) for o in again["orders"]] == [
        (o["order_id"], o["group"]) for o in data["orders"]
    ]
    with deps["engine"].connect() as con:
        stored = con.execute(select(func.count()).select_from(ABAssignment)).scalar()
    assert stored == len(data["orders"])


def test_risk_batch_empty_day(ctx):
    client, _ = ctx
    r = client.post("/risk/batch", json={"date": date(2030, 1, 1).isoformat()}, headers=H)
    assert r.json()["orders"] == []


def test_metrics_contract(ctx):
    client, _ = ctx
    r = client.get("/metrics?period=week", headers=H)
    assert r.status_code == 200
    data = r.json()
    assert data["period"] == "week"
    assert data["drafts"] >= 1 and data["feedback"] >= 1
    assert 0 <= data["approval_without_edit_rate"] <= 1
    assert sum(data["tickets_by_category"].values()) >= 4
    assert client.get("/metrics?period=year", headers=H).status_code == 422


def test_correlation_id_is_echoed(ctx):
    client, _ = ctx
    r = client.get("/health", headers={"x-correlation-id": "abc-123"})
    assert r.headers["x-correlation-id"] == "abc-123"
