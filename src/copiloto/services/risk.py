"""Lote diário de pedidos de alto risco, com sorteio do A/B registrado no banco."""

from dataclasses import dataclass
from datetime import date

import joblib
import pandas as pd
from sqlalchemy.orm import Session

from copiloto.db.models import ABAssignment
from copiloto.ds.experiment.assignment import assign_group
from copiloto.ds.risk.explain import explain_order, shap_values
from copiloto.integrations.orders import OrderSource


@dataclass
class RiskModel:
    """Modelo de risco salvo na Fase 2 (LightGBM + calibrador + limiar)."""

    bundle: dict

    @classmethod
    def load(cls, path) -> "RiskModel":  # noqa: ANN001
        return cls(joblib.load(path))

    @property
    def threshold(self) -> float:
        return float(self.bundle["threshold"])

    def score(self, orders: pd.DataFrame) -> pd.Series:
        raw = self.bundle["model"].predict_proba(orders)
        return pd.Series(self.bundle["calibrator"].transform(raw), index=orders.index)

    def reasons(self, orders: pd.DataFrame, top: int = 3) -> dict:
        values, _ = shap_values(self.bundle["model"], orders)
        view = self.bundle["model"].transform(orders)
        return {i: explain_order(values, view, i, top) for i in orders.index}


@dataclass
class RiskBatchService:
    model: RiskModel
    orders: OrderSource
    seed: int
    max_per_day: int

    def run(self, session: Session, day: date) -> list[dict]:
        """Pontua os pedidos entregues no dia, sorteia tratamento e controle e grava os grupos.

        Os dois grupos são devolvidos e registrados; só o tratamento é contatado (n8n).
        O limite diário vale para o tratamento, que é o que gera custo.
        """
        delivered = self.orders.delivered_on(day)
        if delivered.empty:
            return []
        delivered = delivered.assign(probability=self.model.score(delivered))
        high = delivered[delivered["probability"] >= self.model.threshold]
        high = high.sort_values("probability", ascending=False)
        if high.empty:
            return []
        reasons = self.model.reasons(high)
        out, treated = [], 0
        for idx, row in high.iterrows():
            order_id = str(row["order_id"])
            existing = session.get(ABAssignment, order_id)
            group = existing.group if existing else assign_group(order_id, self.seed)
            if group == "treatment":
                if treated >= self.max_per_day:
                    continue
                treated += 1
            if existing is None:
                session.add(
                    ABAssignment(
                        order_id=order_id,
                        group=group,
                        probability=float(row["probability"]),
                        batch_date=day.isoformat(),
                        seed=self.seed,
                    )
                )
            out.append(
                {
                    "order_id": order_id,
                    "probability": round(float(row["probability"]), 4),
                    "group": group,
                    "reasons": [
                        {"feature": r["feature"], "value": r["value"], "direction": r["direction"]}
                        for r in reasons[idx]
                    ],
                }
            )
        session.commit()
        return out
