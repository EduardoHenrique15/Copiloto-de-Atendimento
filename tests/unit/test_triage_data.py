import pandas as pd
import pytest

from copiloto.ai.triage import data as triage_data
from copiloto.ai.triage.data import GoldNotReadyError, complaint_texts, load_gold


def test_complaint_texts_joins_title():
    df = pd.DataFrame({"comment_title": ["Atraso", None], "comment_message": ["demorou", "ok"]})
    assert complaint_texts(df).tolist() == ["[Atraso] demorou", "ok"]


def test_gold_must_be_complete(tmp_path, monkeypatch):
    labels = tmp_path
    pd.DataFrame(
        {"complaint_id": ["a", "b"], "split": ["val", "val"], "repeat": False, "order": [0, 1]}
    ).to_csv(labels / "gold_sample.csv", index=False)
    pd.DataFrame(
        [
            {
                "complaint_id": "a",
                "round": 1,
                "label": "outro",
                "multiple_problems": False,
                "labeled_at": "2026-11-01T00:00:00",
                "labeler": "eduardo",
            }
        ]
    ).to_csv(labels / "gold.csv", index=False)
    monkeypatch.setattr(
        triage_data,
        "load_complaints",
        lambda _: pd.DataFrame(
            {
                "complaint_id": ["a", "b"],
                "comment_title": [None, None],
                "comment_message": ["x", "y"],
            }
        ),
    )
    with pytest.raises(GoldNotReadyError, match="Faltam 1 de 2"):
        load_gold(labels, tmp_path / "db", "val")
