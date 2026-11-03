"""Identidade visual das ferramentas Streamlit: tipografia, cores e componentes em cartão.

Paleta: papel quente ao fundo, tinta azul-escura no texto, verde-petróleo como cor de ação,
âmbar para atenção e vermelho só para alerta. Números em fonte monoespaçada, para alinhar.
"""

from html import escape

import streamlit as st

INK = "#1C2433"
MUTED = "#5B6472"
ACCENT = "#0F766E"
WARN = "#B45309"
DANGER = "#B42318"
LINE = "#E2DDD2"
CARD = "#FFFFFF"

_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');
html, body, [class*="css"], .stMarkdown, .stButton button, .stRadio, input, textarea {{
  font-family: 'IBM Plex Sans', system-ui, sans-serif;
}}
.block-container {{ padding-top: 2.2rem; max-width: 1080px; }}
h1, h2, h3 {{ color: {INK}; letter-spacing: -0.01em; }}
.cp-eyebrow {{ color: {ACCENT}; font-size: .78rem; font-weight: 600; letter-spacing: .08em;
  text-transform: uppercase; margin-bottom: .2rem; }}
.cp-title {{ font-size: 1.9rem; font-weight: 600; color: {INK}; line-height: 1.2; margin: 0; }}
.cp-sub {{ color: {MUTED}; margin: .35rem 0 1.4rem; font-size: 1rem; }}
.cp-section {{ font-size: .82rem; font-weight: 600; color: {MUTED}; text-transform: uppercase;
  letter-spacing: .07em; border-bottom: 1px solid {LINE}; padding-bottom: .4rem;
  margin: 1.8rem 0 .9rem; }}
.cp-card {{ background: {CARD}; border: 1px solid {LINE}; border-radius: 10px;
  padding: .9rem 1rem; height: 100%; }}
.cp-card .label {{ color: {MUTED}; font-size: .8rem; }}
.cp-card .value {{ font-family: 'IBM Plex Mono', monospace; font-size: 1.55rem; color: {INK};
  margin-top: .15rem; }}
.cp-card .hint {{ color: {MUTED}; font-size: .78rem; margin-top: .2rem; }}
.cp-card.warn {{ border-left: 4px solid {WARN}; }}
.cp-card.danger {{ border-left: 4px solid {DANGER}; }}
.cp-card.ok {{ border-left: 4px solid {ACCENT}; }}
.cp-quote {{ background: {CARD}; border: 1px solid {LINE}; border-left: 4px solid {INK};
  border-radius: 8px; padding: 1rem 1.1rem; font-size: 1.05rem; color: {INK}; }}
.cp-empty {{ border: 1px dashed {LINE}; border-radius: 10px; padding: 1.2rem; color: {MUTED};
  text-align: center; }}
.cp-pill {{ display: inline-block; border: 1px solid {LINE}; border-radius: 999px;
  padding: .1rem .6rem; font-size: .78rem; color: {MUTED}; margin-right: .3rem;
  background: {CARD}; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {LINE}; }}
.stButton button {{ border-radius: 8px; border: 1px solid {LINE}; }}
.stButton button:hover {{ border-color: {ACCENT}; color: {ACCENT}; }}
</style>
"""


def apply(page_title: str, layout: str = "centered") -> None:
    st.set_page_config(page_title=page_title, layout=layout)
    st.markdown(_CSS, unsafe_allow_html=True)


def header(title: str, subtitle: str = "", eyebrow: str = "Copiloto de Atendimento") -> None:
    st.markdown(
        f'<div class="cp-eyebrow">{escape(eyebrow)}</div>'
        f'<h1 class="cp-title">{escape(title)}</h1>'
        + (f'<p class="cp-sub">{escape(subtitle)}</p>' if subtitle else ""),
        unsafe_allow_html=True,
    )


def section(title: str) -> None:
    st.markdown(f'<div class="cp-section">{escape(title)}</div>', unsafe_allow_html=True)


def card(label: str, value: str, hint: str = "", tone: str = "") -> None:
    """Cartão de indicador. `tone`: "", "ok", "warn" ou "danger"."""
    st.markdown(
        f'<div class="cp-card {tone}"><div class="label">{escape(label)}</div>'
        f'<div class="value">{escape(value)}</div>'
        + (f'<div class="hint">{escape(hint)}</div>' if hint else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def quote(text: str) -> None:
    st.markdown(f'<div class="cp-quote">{escape(text)}</div>', unsafe_allow_html=True)


def empty(text: str) -> None:
    st.markdown(f'<div class="cp-empty">{escape(text)}</div>', unsafe_allow_html=True)


def pills(items: list[str]) -> None:
    st.markdown(
        "".join(f'<span class="cp-pill">{escape(i)}</span>' for i in items),
        unsafe_allow_html=True,
    )
