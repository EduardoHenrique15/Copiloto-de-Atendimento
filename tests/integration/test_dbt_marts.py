"""Roda o dbt na amostra fictícia e confere os marts contra valores calculados à mão.

A amostra está em tests/data/olist/raw. Os valores esperados estão comentados
em cada teste, para que qualquer pessoa consiga refazer a conta.
"""

import shutil
import sys
from pathlib import Path

import duckdb
import pytest

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_RAW = ROOT / "tests" / "data" / "olist" / "raw"
sys.path.insert(0, str(ROOT / "scripts"))

from dbt_build import build  # noqa: E402

pytestmark = pytest.mark.integration

# Na amostra, 2 de 7 avaliações não têm comentário (r1 vazio e r6b só com espaços).
SAMPLE_EMPTY_RATE_VARS = "{expected_empty_comment_rate: 0.286}"


@pytest.fixture(scope="module")
def db(tmp_path_factory):
    data_dir = tmp_path_factory.mktemp("dados")
    shutil.copytree(SAMPLE_RAW, data_dir / "raw")
    code = build(data_dir, SAMPLE_EMPTY_RATE_VARS, target_path=data_dir / "dbt_target")
    assert code == 0, "dbt build falhou na amostra fictícia"
    con = duckdb.connect(str(data_dir / "processed" / "copiloto.duckdb"), read_only=True)
    yield con
    con.close()


def _rows(con, sql):
    cur = con.execute(sql)
    cols = [d[0] for d in cur.description]
    return [dict(zip(cols, row, strict=True)) for row in cur.fetchall()]


def _by_order(con, table):
    return {r["order_id"]: r for r in _rows(con, f"select * from marts.{table}")}


def test_risk_mart_keeps_only_delivered_and_reviewed_orders(db):
    # o5 foi cancelado; o7 foi entregue mas não tem avaliação.
    assert set(_by_order(db, "fct_orders_risk")) == {"o1", "o2", "o3", "o4", "o6"}


def test_target_uses_latest_review(db):
    risk = _by_order(db, "fct_orders_risk")
    # o6 tem duas avaliações: r6a (nota 4) e r6b (nota 2, mais recente).
    assert risk["o6"]["review_score"] == 2
    assert risk["o6"]["is_negative"] is True
    assert risk["o4"]["is_negative"] is False  # nota 3 não é negativa
    assert risk["o2"]["is_negative"] is True


def test_delay_metrics(db):
    risk = _by_order(db, "fct_orders_risk")
    # o2: estimado 20/01 00:00, entregue 25/01 15:00 = 5,625 dias de atraso.
    assert risk["o2"]["is_late"] is True
    assert risk["o2"]["delay_days"] == pytest.approx(5.625)
    # o1: estimado 15/01, entregue 08/01 15:00 = 6,375 dias adiantado.
    assert risk["o1"]["is_late"] is False
    assert risk["o1"]["delay_days"] == pytest.approx(-6.375)
    # o1: compra 02/01 10:00, estimado 15/01 00:00 = 12,583 dias prometidos.
    assert risk["o1"]["promised_days"] == pytest.approx(12 + 14 / 24)


def test_multi_seller_order_uses_most_expensive_item(db):
    o4 = _by_order(db, "fct_orders_risk")["o4"]
    # o4: item de s2 (R$ 100) e item de s1 (R$ 20).
    assert o4["seller_id"] == "s2"
    assert o4["n_sellers"] == 2
    assert o4["main_category"] == "health_beauty"
    assert o4["main_payment_type"] == "credit_card"
    assert o4["n_payment_types"] == 2
    assert o4["freight_ratio"] == pytest.approx(25 / 120)


def test_seller_history_is_as_of_purchase(db):
    risk = _by_order(db, "fct_orders_risk")
    # o1 é o primeiro pedido de s1: sem histórico.
    assert risk["o1"]["seller_prior_orders"] == 0
    assert risk["o1"]["seller_prior_avg_score"] is None
    # o3 (compra 20/01): antes dele, s1 tinha o1 e o2. Só a avaliação de o1
    # (09/01) existia; a de o2 é de 26/01. Só o1 tinha sido entregue (no prazo).
    assert risk["o3"]["seller_prior_orders"] == 2
    assert risk["o3"]["seller_prior_avg_score"] == pytest.approx(5.0)
    assert risk["o3"]["seller_prior_late_rate"] == pytest.approx(0.0)
    # o6 (compra 01/03): s1 vendeu em o1..o5 (inclui o item de o4 e o cancelado o5).
    # Notas conhecidas: 5, 1, 2, 3, 1 = média 2,4. Entregues: o1, o2, o3, o4,
    # dos quais o2 e o4 atrasaram = 0,5.
    assert risk["o6"]["seller_prior_orders"] == 5
    assert risk["o6"]["seller_prior_avg_score"] == pytest.approx(2.4)
    assert risk["o6"]["seller_prior_late_rate"] == pytest.approx(0.5)
    # o4 tem s2 como vendedor principal, que não vendeu nada antes.
    assert risk["o4"]["seller_prior_orders"] == 0


def test_no_feature_after_cutoff(db):
    # Toda data usada como feature precisa ser anterior ou igual ao corte (entrega).
    bad = _rows(
        db,
        """
        select order_id from marts.fct_orders_risk
        where purchased_at > feature_cutoff_at
           or estimated_delivery_at is null
        """,
    )
    assert bad == []


def test_distance_uses_average_coordinates_inside_brazil(db):
    risk = _by_order(db, "fct_orders_risk")
    # o1: cliente 01002 e vendedor 01001 (mesma cidade): poucos km.
    assert risk["o1"]["same_state"] is True
    assert 0 < risk["o1"]["distance_km"] < 5
    # o2: cliente em BH (30001). O ponto fora do Brasil é descartado; se não
    # fosse, a distância passaria de 9.000 km.
    assert 450 < risk["o2"]["distance_km"] < 550
    assert risk["o2"]["same_state"] is False


def test_complaints_have_text_and_low_score(db):
    complaints = _rows(db, "select * from marts.fct_complaints order by review_id")
    # r6b tem só espaços e r6a tem nota 4: ficam de fora.
    assert [c["review_id"] for c in complaints] == ["r2", "r3", "r4", "r5"]
    assert all(c["review_score"] <= 3 for c in complaints)
    # O comentário com quebra de linha e vírgula é lido inteiro.
    r2 = complaints[0]
    assert "\n" in r2["comment_message"]
    assert r2["comment_message"].endswith("meus e-mails")
    assert "ninguém" in r2["comment_message"]


def test_causal_mart_has_treatment_for_every_row(db):
    causal = _by_order(db, "fct_orders_causal")
    assert set(causal) == {"o1", "o2", "o3", "o4", "o6"}
    assert {k: v["is_late"] for k, v in causal.items()} == {
        "o1": False,
        "o2": True,
        "o3": False,
        "o4": True,
        "o6": False,
    }


def test_zip_prefix_keeps_leading_zero(db):
    zips = {
        r["zip_prefix"]
        for r in _rows(db, "select zip_prefix from intermediate.int_zip_coordinates")
    }
    assert "01001" in zips
