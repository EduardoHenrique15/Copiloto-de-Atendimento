from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from copiloto.ai.labeling.gold import GoldStore, make_gold_sample, pending, self_agreement
from copiloto.ai.taxonomy import BY_NUMBER, CATEGORIES, CATEGORY_KEYS, urgency

T0 = datetime(2026, 11, 1, 12, tzinfo=UTC)


def _complaints(n=1000):
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "complaint_id": [f"c{i:04d}" for i in range(n)],
            "review_score": rng.choice([1, 2, 3], n),
            "review_created_at": pd.Timestamp("2017-01-01")
            + pd.to_timedelta(rng.integers(0, 600, n), unit="D"),
        }
    )


def test_taxonomy_has_nine_numbered_categories():
    assert len(CATEGORIES) == 9
    assert sorted(BY_NUMBER) == list(range(1, 10))
    assert "sem_problema" in CATEGORY_KEYS and "cancelamento_ou_cobranca" in CATEGORY_KEYS


@pytest.mark.parametrize(
    ("category", "text", "delay", "status", "expected"),
    [
        ("nao_recebido", "não chegou", -5, "delivered", "alta"),
        ("nao_recebido", "não chegou", 12, "shipped", "alta"),
        ("nao_recebido", "não chegou", 3, "shipped", "media"),
        ("produto_errado_ou_incompleto", "vou ao PROCON", -3, "delivered", "alta"),
        ("cancelamento_ou_cobranca", "não estornaram", None, "canceled", "alta"),
        ("atraso_entrega", "demorou", 5, "delivered", "media"),
        ("outro", "frete caro", -2, "delivered", "baixa"),
        ("sem_problema", "muito bom", -2, "delivered", "baixa"),
    ],
)
def test_urgency_rule(category, text, delay, status, expected):
    assert urgency(category, text, delay, status) == expected


def test_gold_sample_split_repeat_and_exclusion():
    df = _complaints()
    excluded = {"c0000", "c0001"}
    s = make_gold_sample(df, exclude=excluded)
    assert len(s) == 300
    assert s["split"].value_counts().to_dict() == {"test": 200, "val": 100}
    assert int(s["repeat"].sum()) == 50
    assert not excluded & set(s["complaint_id"])
    assert s.equals(make_gold_sample(df, exclude=excluded))


def test_store_saves_overwrites_and_removes(tmp_path):
    store = GoldStore(tmp_path / "gold.csv")
    store.save_label("c1", 1, "atraso_entrega", False, now=T0)
    store.save_label("c1", 1, "nao_recebido", True, now=T0)
    labels = store.load()
    assert len(labels) == 1
    assert labels.loc[0, "label"] == "nao_recebido"
    assert bool(labels.loc[0, "multiple_problems"])
    store.remove_label("c1", 1)
    assert store.load().empty


def test_store_rejects_unknown_label(tmp_path):
    with pytest.raises(ValueError):
        GoldStore(tmp_path / "g.csv").save_label("c1", 1, "inventado", False)


def test_store_never_saves_text(tmp_path):
    store = GoldStore(tmp_path / "gold.csv")
    store.save_label("c1", 1, "outro", False, now=T0)
    assert list(store.load().columns) == [
        "complaint_id",
        "round",
        "label",
        "multiple_problems",
        "labeled_at",
        "labeler",
    ]


def test_repeat_round_waits_seven_days(tmp_path):
    sample = pd.DataFrame(
        {
            "complaint_id": ["a", "b"],
            "split": ["val", "val"],
            "repeat": [True, False],
            "order": [0, 1],
        }
    )
    store = GoldStore(tmp_path / "gold.csv")
    assert pending(sample, store.load(), 1) == ["a", "b"]
    store.save_label("a", 1, "outro", False, now=T0)
    store.save_label("b", 1, "outro", False, now=T0)
    assert pending(sample, store.load(), 1) == []
    assert pending(sample, store.load(), 2, now=T0 + timedelta(days=6)) == []
    assert pending(sample, store.load(), 2, now=T0 + timedelta(days=7)) == ["a"]


def test_self_agreement(tmp_path):
    store = GoldStore(tmp_path / "gold.csv")
    pairs = [
        ("a", "outro", "outro"),
        ("b", "nao_recebido", "nao_recebido"),
        ("c", "atraso_entrega", "nao_recebido"),
        ("d", "sem_problema", "sem_problema"),
    ]
    for cid, r1, r2 in pairs:
        store.save_label(cid, 1, r1, False, now=T0)
        store.save_label(cid, 2, r2, False, now=T0 + timedelta(days=8))
    result = self_agreement(store.load())
    assert result["n"] == 4
    assert result["raw_agreement"] == pytest.approx(0.75)
    assert 0 < result["kappa"] < 1
    assert result["disagreements"] == [
        {"complaint_id": "c", "round_1": "atraso_entrega", "round_2": "nao_recebido"}
    ]
