"""O limite diário do A/B vale para os dois grupos, antes do sorteio (sem viés de seleção)."""

from datetime import date

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from copiloto.db.models import ABAssignment, Base
from copiloto.db.session import make_engine
from copiloto.ds.experiment.assignment import assign_group
from copiloto.services.risk import RiskBatchService

DAY = date(2018, 6, 3)


class StubModel:
    threshold = 0.5

    def score(self, orders):  # noqa: ANN001, ANN201
        return orders["p"]

    def reasons(self, orders, top=3):  # noqa: ANN001, ANN201
        return {i: [] for i in orders.index}


class StubOrders:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame

    def delivered_on(self, day):  # noqa: ANN001, ANN201
        return self.frame


def _run(n_orders: int, cap: int):
    frame = pd.DataFrame(
        {
            "order_id": [f"o{i:03d}" for i in range(n_orders)],
            "p": [0.99 - i * 0.001 for i in range(n_orders)],
        }
    )
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    service = RiskBatchService(StubModel(), StubOrders(frame), seed=42, max_per_day=cap)
    with Session(engine) as db:
        out = service.run(db, DAY)
        stored = db.scalars(select(ABAssignment)).all()
        return frame, out, stored


def test_cap_applies_to_both_groups_before_assignment():
    frame, out, stored = _run(n_orders=100, cap=5)
    top = set(frame["order_id"].head(10))  # ceil(5 / 0,5) = 10 de maior risco
    assert {o["order_id"] for o in out} == top
    assert {s.order_id for s in stored} == top
    # o controle vem do mesmo conjunto de risco que o tratamento
    assert {o["group"] for o in out} == {"treatment", "control"}


def test_excess_treatment_stays_in_group_without_contact():
    _, out, stored = _run(n_orders=100, cap=5)
    treatment = [o for o in out if o["group"] == "treatment"]
    contacted = [o for o in out if o["contact"]]
    assert len(contacted) == min(5, len(treatment))
    assert all(o["group"] == "treatment" for o in contacted)
    by_id = {s.order_id: s for s in stored}
    assert all(by_id[o["order_id"]].contacted == o["contact"] for o in out)
    assert all(o["group"] == assign_group(o["order_id"], 42) for o in out)
