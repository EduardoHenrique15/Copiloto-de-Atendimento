"""A ferramenta de rotulagem funciona de ponta a ponta sobre a amostra fictícia."""

import shutil
import sys
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "src" / "copiloto" / "dashboard" / "labeling_app.py"
sys.path.insert(0, str(ROOT / "scripts"))

from dbt_build import build  # noqa: E402

pytestmark = pytest.mark.integration


@pytest.fixture
def app(tmp_path, monkeypatch):
    data_dir = tmp_path / "dados"
    shutil.copytree(ROOT / "tests" / "data" / "olist" / "raw", data_dir / "raw")
    assert build(data_dir, "{expected_empty_comment_rate: 0.286}", tmp_path / "t") == 0
    labels = tmp_path / "labels"
    labels.mkdir()
    import duckdb

    con = duckdb.connect(str(data_dir / "processed" / "copiloto.duckdb"), read_only=True)
    ids = [r[0] for r in con.execute("select complaint_id from marts.fct_complaints").fetchall()]
    con.close()
    pd.DataFrame(
        {"complaint_id": ids, "split": "val", "repeat": False, "order": range(len(ids))}
    ).to_csv(labels / "gold_sample.csv", index=False)
    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("LABELS_DIR", str(labels))
    from copiloto.core.config import get_settings

    get_settings.cache_clear()
    yield AppTest.from_file(str(APP), default_timeout=30), labels, len(ids)
    get_settings.cache_clear()


def test_labeling_saves_label_skip_and_undo(app):
    at, labels, n = app
    at.run()
    assert not at.exception
    assert f"faltam {n}" in at.caption[0].value

    at.checkbox(key="multi").check()
    next(b for b in at.button if b.label.startswith("2.")).click()
    at.run()
    gold = pd.read_csv(labels / "gold.csv")
    assert gold.loc[0, "label"] == "nao_recebido"
    assert bool(gold.loc[0, "multiple_problems"])
    assert f"faltam {n - 1}" in at.caption[0].value

    first_pending = at.caption[0].value
    next(b for b in at.button if b.label.startswith("Pular")).click()
    at.run()
    assert at.caption[0].value != first_pending

    next(b for b in at.button if b.label.startswith("Desfazer último")).click()
    at.run()
    assert pd.read_csv(labels / "gold.csv").empty
