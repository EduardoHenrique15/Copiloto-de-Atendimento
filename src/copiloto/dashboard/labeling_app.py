"""Ferramenta de rotulagem humana do conjunto ouro.

Uso: streamlit run src/copiloto/dashboard/labeling_app.py

Atalhos: 1 a 9 escolhem a categoria; m marca "mais de um problema";
p pula (o item volta no fim); z desfaz o último rótulo.
"""

import os
from pathlib import Path

import pandas as pd
import streamlit as st
from streamlit_shortcuts import add_shortcuts, shortcut_button

from copiloto.ai.labeling.gold import GoldStore, pending
from copiloto.ai.labeling.sampling import load_complaints
from copiloto.ai.taxonomy import CATEGORIES
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[3]
# A variável LABELS_DIR existe só para os testes apontarem para uma pasta temporária.
LABELS_DIR = Path(os.getenv("LABELS_DIR", ROOT / "data" / "labels"))
SAMPLE_PATH = LABELS_DIR / "gold_sample.csv"
GOLD_PATH = LABELS_DIR / "gold.csv"


@st.cache_data
def load_texts() -> dict[str, str]:
    """Título e comentário de cada reclamação, lidos do DuckDB local."""
    df = load_complaints(get_settings().duckdb_path)
    title = df["comment_title"].fillna("")
    text = (title.where(title == "", "[" + title + "] ") + df["comment_message"]).str.strip()
    return dict(zip(df["complaint_id"], text, strict=True))


def main() -> None:
    st.set_page_config(page_title="Rotulagem", layout="centered")
    st.title("Rotulagem de reclamações")

    if not SAMPLE_PATH.exists():
        st.error("Amostra não encontrada. Rode antes: python scripts/make_gold_sample.py")
        return
    sample = pd.read_csv(SAMPLE_PATH, dtype={"complaint_id": str})
    store = GoldStore(GOLD_PATH)
    texts = load_texts()
    state = st.session_state
    state.setdefault("skipped", [])
    state.setdefault("history", [])

    round_ = st.sidebar.radio(
        "Rodada",
        [1, 2],
        format_func=lambda r: "1: rotulagem principal" if r == 1 else "2: repetição (kappa)",
    )
    labels = store.load()
    todo = pending(sample, labels, round_)
    todo = [c for c in todo if c not in state.skipped] + [c for c in state.skipped if c in todo]

    total = len(sample) if round_ == 1 else int(sample["repeat"].sum())
    done = int((labels["round"] == round_).sum())
    st.sidebar.metric("Rotulados nesta rodada", f"{done} de {total}")
    st.sidebar.progress(done / total if total else 0.0)
    with st.sidebar.expander("Categorias (resumo do guia)"):
        for c in CATEGORIES:
            st.markdown(f"**{c.number}. {c.name}**: {c.description}")
    st.sidebar.caption("Guia completo: data/labels/guia-de-rotulos.md")

    if not todo:
        if round_ == 2:
            st.info("Nenhum item disponível. A repetição libera cada item 7 dias depois do rótulo.")
        else:
            st.success("Rodada concluída. Obrigado!")
        return

    cid = todo[0]
    st.caption(f"Item {cid[:8]} · faltam {len(todo)}")
    st.markdown(f"> {texts.get(cid, '(texto não encontrado no DuckDB)')}")

    if state.pop("reset_multi", False):
        state.multi = False
    multi = st.checkbox("Mais de um problema (m)", key="multi")
    cols = st.columns(3)
    for i, c in enumerate(CATEGORIES):
        with cols[i % 3]:
            if shortcut_button(f"{c.number}. {c.name}", str(c.number), use_container_width=True):
                store.save_label(cid, round_, c.key, multi)
                state.history.append((cid, round_))
                if cid in state.skipped:
                    state.skipped.remove(cid)
                state.reset_multi = True
                st.rerun()

    left, right = st.columns(2)
    with left:
        if shortcut_button("Pular", "p"):
            if cid not in state.skipped:
                state.skipped.append(cid)
            st.rerun()
    with right:
        if shortcut_button("Desfazer último", "z") and state.history:
            last_id, last_round = state.history.pop()
            store.remove_label(last_id, last_round)
            st.rerun()
    add_shortcuts(multi="m")


if __name__ == "__main__":
    main()
