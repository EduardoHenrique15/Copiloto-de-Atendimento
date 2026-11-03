"""Painel de métricas do Copiloto (seção 8.6): operação ao vivo e qualidade medida offline.

Uso: streamlit run src/copiloto/dashboard/metrics_app.py
Lê o banco operacional (DATABASE_URL) e os resultados versionados em eval/results/.
"""

import json
import os
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from copiloto.ai.taxonomy import BY_KEY
from copiloto.dashboard import theme
from copiloto.services.metrics import check_alerts, compute_metrics

ROOT = Path(__file__).resolve().parents[3]
# A variável RESULTS_DIR existe só para os testes apontarem para uma pasta temporária.
RESULTS = Path(os.getenv("RESULTS_DIR", ROOT / "eval" / "results"))


def brl(v: float | None) -> str:
    return (
        "—" if v is None else f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )


def pct(v: float | None) -> str:
    return "—" if v is None else f"{v:.1%}".replace(".", ",")


def secs(v: float | None) -> str:
    return "—" if v is None else f"{v / 1000:.1f} s".replace(".", ",")


def load_json(name: str) -> dict | None:
    path = RESULTS / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


@st.cache_resource
def sessions():
    from copiloto.core.config import get_settings
    from copiloto.db.session import make_engine, session_factory

    return session_factory(make_engine(get_settings().database_url))


def live_section() -> None:
    from copiloto.core.config import get_settings

    settings = get_settings()
    theme.section("Operação")
    period = (
        st.segmented_control(
            "Período",
            ["day", "week"],
            default="day",
            format_func=lambda p: "Últimas 24 horas" if p == "day" else "Últimos 7 dias",
            label_visibility="collapsed",
        )
        or "day"
    )
    try:
        with sessions()() as db:
            m = compute_metrics(db, period)
    except Exception:  # noqa: BLE001 - banco fora do ar não pode derrubar o painel
        theme.empty("Banco operacional indisponível. Suba a API com: docker compose up -d")
        return

    alerts = (
        {
            a["name"]: a
            for a in check_alerts(
                m,
                settings.alert_max_daily_cost_brl,
                settings.alert_max_p95_latency_ms,
                settings.alert_max_guardrail_rate,
            )
        }
        if period == "day"
        else {}
    )

    def tone(name: str) -> str:
        a = alerts.get(name)
        return "" if a is None or a["value"] is None else ("danger" if a["breached"] else "ok")

    tickets = sum(m["tickets_by_category"].values())
    cols = st.columns(4)
    with cols[0]:
        theme.card("Tickets triados", f"{tickets}", f"{m['drafts']} rascunhos")
    with cols[1]:
        theme.card(
            "Custo do LLM",
            brl(m["cost_brl"]),
            f"{m['llm_calls']} chamadas",
            tone("custo do dia (R$)"),
        )
    with cols[2]:
        theme.card(
            "Latência p95",
            secs(m["latency_p95_ms"]),
            f"p50 {secs(m['latency_p50_ms'])}",
            tone("latência p95 (ms)"),
        )
    with cols[3]:
        theme.card(
            "Bloqueio por guardrail",
            pct(m["guardrail_block_rate"]),
            f"aprovados sem edição: {pct(m['approval_without_edit_rate'])}",
            tone("taxa de bloqueio dos guardrails"),
        )
    breached = [a for a in alerts.values() if a["breached"]]
    if breached:
        st.markdown(" ")
        st.error("Limite passado: " + "; ".join(a["name"] for a in breached))

    st.markdown(" ")
    if tickets:
        data = pd.DataFrame(
            sorted(
                (
                    (BY_KEY[k].name if k in BY_KEY else k, n)
                    for k, n in m["tickets_by_category"].items()
                ),
                key=lambda kv: -kv[1],
            ),
            columns=["categoria", "tickets"],
        )
        chart = (
            alt.Chart(data)
            .mark_bar(color=theme.ACCENT, cornerRadiusEnd=3, height=18)
            .encode(
                x=alt.X("tickets:Q", title=None, axis=alt.Axis(grid=False, tickMinStep=1)),
                y=alt.Y("categoria:N", sort="-x", title=None, axis=alt.Axis(labelLimit=240)),
                tooltip=["categoria", "tickets"],
            )
            .properties(height=36 * len(data))
            .configure_view(strokeWidth=0)
            .configure_axis(labelColor=theme.MUTED, domainColor=theme.LINE, labelFontSize=12)
        )
        st.altair_chart(chart, width="stretch")
    else:
        theme.empty("Nenhum ticket no período. Simule com: python scripts/simulate_tickets.py")


def offline_section() -> None:
    theme.section("Qualidade medida offline")
    triage = load_json("triage_comparison_test.json")
    copilot = load_json("copilot_eval.json")
    risk = load_json("risk_metrics.json")
    cols = st.columns(3)
    with cols[0]:
        if triage and "zero_shot" in triage:
            q, r = triage["zero_shot"]["quality"], triage["zero_shot"]["routing"]
            theme.card(
                "Triagem: acurácia no teste",
                pct(q["accuracy"]),
                f"{pct(r['coverage'])} automáticos, {pct(r['accuracy_auto'])} de acerto",
            )
        else:
            theme.empty("Triagem ainda não avaliada")
    with cols[1]:
        if copilot:
            c = copilot["checks"]
            hint = f"citação {pct(c['citation']['rate'])}"
            if "agreement" in copilot and copilot["agreement"]["acceptable"]:
                hint += f" · juiz: {pct(copilot['judge']['all_pass_rate'])} aprovados"
            theme.card("Copiloto: ação correta", pct(c["action"]["rate"]), hint)
        else:
            theme.empty("Copiloto ainda não avaliado")
    with cols[2]:
        if risk:
            t = risk["metrics_test"]
            theme.card(
                "Risco: PR-AUC no teste",
                f"{t['lightgbm']['pr_auc']:.3f}".replace(".", ","),
                f"regra simples: {t['baseline']['pr_auc']:.3f}".replace(".", ","),
            )
        else:
            theme.empty("Modelo de risco ainda não treinado")
    st.caption("Números gerados pelos scripts em scripts/ e versionados em eval/results/.")


def main() -> None:
    theme.apply("Copiloto · Painel", layout="wide")
    theme.header(
        "Painel do atendimento",
        "Volume, custo, latência e guardrails da operação, ao lado da qualidade medida nos testes.",
    )
    live_section()
    offline_section()


if __name__ == "__main__":
    main()
