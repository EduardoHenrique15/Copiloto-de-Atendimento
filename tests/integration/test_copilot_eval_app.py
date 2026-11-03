"""A ferramenta de avaliação humana do copiloto grava a rubrica e avança para o próximo caso."""

import json
import shutil
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from copiloto.ai.eval.cases import load_cases, select_for_human
from copiloto.ai.eval.judge import CRITERIA

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "copiloto" / "dashboard" / "copilot_eval_app.py"

pytestmark = pytest.mark.integration


@pytest.fixture
def app(tmp_path, monkeypatch):
    eval_dir = tmp_path / "eval"
    (eval_dir / "results").mkdir(parents=True)
    shutil.copy(ROOT / "eval" / "copilot_cases.yaml", eval_dir / "copilot_cases.yaml")
    chosen = select_for_human(load_cases(eval_dir / "copilot_cases.yaml"))
    with (eval_dir / "results" / "copilot_drafts_draft-v1.jsonl").open("w", encoding="utf-8") as f:
        for case_id in chosen[:2]:
            draft = {
                "case_id": case_id,
                "response": "Olá! Rascunho de teste.",
                "policies_cited": ["tom-de-voz#como-escrever"],
                "suggested_action": "nenhuma",
                "needs_human": False,
                "retrieved": [
                    "tom-de-voz#como-escrever",
                    "reembolso#prazos-por-forma-de-pagamento",
                ],
            }
            f.write(json.dumps(draft, ensure_ascii=False) + "\n")
    monkeypatch.setenv("EVAL_DIR", str(eval_dir))
    return AppTest.from_file(str(APP), default_timeout=30), eval_dir, chosen[:2]


def test_saves_rubric_and_moves_on(app):
    at, eval_dir, ids = app
    at.run()
    assert not at.exception
    assert "faltam 2" in at.caption[0].value
    assert f"Caso {ids[0]}" in at.subheader[0].value

    at.button[0].click()  # salvar sem responder: não grava
    at.run()
    assert at.warning and not (eval_dir / "human" / "copilot_human.csv").exists()

    for i, key in enumerate(CRITERIA):
        at.radio(key=f"{ids[0]}-{key}").set_value("Reprovado" if i == 0 else "Aprovado")
    at.button[0].click()
    at.run()
    saved = pd.read_csv(eval_dir / "human" / "copilot_human.csv")
    assert saved.loc[0, "case_id"] == ids[0]
    assert not saved.loc[0, "fidelidade"] and saved.loc[0, "tom"]
    assert "faltam 1" in at.caption[0].value
    assert f"Caso {ids[1]}" in at.subheader[0].value
