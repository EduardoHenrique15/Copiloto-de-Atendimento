from copiloto.services.metrics import check_alerts, report_text

M = {
    "period": "week",
    "llm_calls": 12,
    "cost_brl": 0.0412,
    "latency_p50_ms": 1200.0,
    "latency_p95_ms": 6100.0,
    "drafts": 5,
    "guardrail_block_rate": 0.2,
    "feedback": 4,
    "approval_without_edit_rate": 0.75,
    "tickets_by_category": {"outro": 1, "nao_recebido": 3, "atraso_entrega": 3},
}


def test_report_text_summarizes_in_portuguese():
    text = report_text(M)
    assert text.startswith("Relatório da semana")
    assert "Tickets triados: 7" in text
    assert "atraso_entrega (3), nao_recebido (3), outro (1)" in text
    assert "R$ 0,04" in text and "p95 6,1 s" in text and "75%" in text


def test_report_text_without_data():
    empty = {
        **M,
        "latency_p50_ms": None,
        "latency_p95_ms": None,
        "guardrail_block_rate": None,
        "approval_without_edit_rate": None,
        "tickets_by_category": {},
    }
    assert "nenhum ticket" in report_text(empty) and "sem dados" in report_text(empty)


def test_alerts_only_when_limit_is_passed():
    alerts = {a["name"]: a for a in check_alerts(M, 5.0, 5000, 0.2)}
    assert alerts["latência p95 (ms)"]["breached"]
    assert not alerts["custo do dia (R$)"]["breached"]
    assert not alerts["taxa de bloqueio dos guardrails"]["breached"]  # igual ao limite não dispara
    none = check_alerts({**M, "latency_p95_ms": None}, 5.0, 5000, 0.2)
    assert not any(a["breached"] for a in none)
