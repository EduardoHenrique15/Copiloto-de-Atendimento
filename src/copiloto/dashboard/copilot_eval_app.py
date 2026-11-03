"""Avaliação humana dos rascunhos do copiloto (40 casos), com a mesma rubrica do juiz.

Uso: streamlit run src/copiloto/dashboard/copilot_eval_app.py

A ferramenta não mostra o veredito do juiz nem as verificações automáticas: a avaliação
humana precisa ser independente para medir a concordância (ADR 0011).
"""

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from copiloto.ai.copilot.policies import load_policies
from copiloto.ai.eval.cases import load_cases, select_for_human
from copiloto.ai.eval.judge import CRITERIA
from copiloto.ai.eval.run import HUMAN_COLUMNS, read_jsonl
from copiloto.dashboard import theme

ROOT = Path(__file__).resolve().parents[3]
# A variável EVAL_DIR existe só para os testes apontarem para uma pasta temporária.
EVAL_DIR = Path(os.getenv("EVAL_DIR", ROOT / "eval"))
CASES = EVAL_DIR / "copilot_cases.yaml"
DRAFTS = EVAL_DIR / "results" / "copilot_drafts.jsonl"
HUMAN = EVAL_DIR / "human" / "copilot_human.csv"
LABELS = {"Aprovado": True, "Reprovado": False}


def load_done() -> pd.DataFrame:
    if HUMAN.exists():
        return pd.read_csv(HUMAN, dtype={"case_id": str})
    return pd.DataFrame(columns=HUMAN_COLUMNS)


def main() -> None:
    theme.apply("Copiloto · Avaliação")
    theme.header(
        "Avaliação dos rascunhos",
        "Mesma rubrica do juiz, sem ver o juiz: aprovado ou reprovado em cada critério.",
    )

    if not DRAFTS.exists():
        st.error(
            "Rascunhos não encontrados. Rode antes: python scripts/evaluate_copilot.py "
            "--stage drafts --allow-llm"
        )
        return
    cases = {c.id: c for c in load_cases(CASES)}
    drafts = {d["case_id"]: d for d in read_jsonl(DRAFTS)}
    chunks = {c.id: c for c in load_policies(ROOT / "policies")}
    selected = [i for i in select_for_human(list(cases.values())) if i in drafts]
    done = load_done()
    pending = [i for i in selected if i not in set(done["case_id"])]

    st.caption(
        f"{len(selected) - len(pending)} de {len(selected)} avaliados; faltam {len(pending)}"
    )
    if not pending:
        st.success("Avaliação concluída. Rode: python scripts/evaluate_copilot.py")
        return

    case_id = pending[0]
    case, draft = cases[case_id], drafts[case_id]
    st.subheader(f"Caso {case_id}")
    theme.section("Reclamação do cliente")
    theme.quote(case.complaint)
    st.code(json.dumps(case.order, ensure_ascii=False), language="json")
    theme.section("Rascunho")
    theme.quote(draft["response"])
    theme.pills(
        [
            f"ação: {draft['suggested_action']}",
            f"precisa de humano: {'sim' if draft['needs_human'] else 'não'}",
        ]
    )
    with st.expander("Políticas que o redator recebeu (as citadas estão marcadas)"):
        for pid in draft["retrieved"]:
            if pid in chunks:
                mark = "✅ citada" if pid in draft["policies_cited"] else "não citada"
                st.markdown(f"**{pid}** ({mark})\n\n{chunks[pid].text}")

    theme.section("Rubrica")
    with st.form(key=f"form-{case_id}"):
        answers = {}
        for key, text in CRITERIA.items():
            answers[key] = st.radio(
                f"{key}: {text}", list(LABELS), index=None, horizontal=True, key=f"{case_id}-{key}"
            )
        note = st.text_input("Observação (opcional)", key=f"{case_id}-nota")
        submitted = st.form_submit_button("Salvar e ir para o próximo")
    if submitted:
        if any(v is None for v in answers.values()):
            st.warning("Marque Aprovado ou Reprovado em todos os critérios.")
            return
        row = {
            "case_id": case_id,
            **{k: LABELS[v] for k, v in answers.items()},
            "nota": note,
            "evaluated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        }
        HUMAN.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([row], columns=HUMAN_COLUMNS).to_csv(
            HUMAN, mode="a", header=not HUMAN.exists(), index=False
        )
        st.rerun()


if __name__ == "__main__":
    main()
