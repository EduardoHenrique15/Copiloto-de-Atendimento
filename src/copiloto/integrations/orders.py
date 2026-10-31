"""Dados dos pedidos, lidos dos marts do DuckDB (sem dados pessoais)."""

from datetime import date
from pathlib import Path
from typing import Protocol

import duckdb
import pandas as pd

ORDER_FIELDS = "order_status, delay_days, items_price, n_items, main_category, is_late"


class OrderSource(Protocol):
    def get(self, order_id: str) -> dict | None: ...

    def delivered_on(self, day: date) -> pd.DataFrame: ...


class DuckDBOrders:
    def __init__(self, path: Path) -> None:
        self.path = path

    def get(self, order_id: str) -> dict | None:
        with duckdb.connect(str(self.path), read_only=True) as con:
            row = con.execute(
                f"select {ORDER_FIELDS} from intermediate.int_orders_enriched where order_id = ?",
                [order_id],
            ).fetchone()
            cols = [d[0] for d in con.description]
        if row is None:
            return None
        return {k: (None if pd.isna(v) else v) for k, v in zip(cols, row, strict=True)}

    def delivered_on(self, day: date) -> pd.DataFrame:
        """Pedidos entregues no dia, com as features do modelo de risco."""
        with duckdb.connect(str(self.path), read_only=True) as con:
            return con.execute(
                "select * from marts.fct_orders_risk where cast(feature_cutoff_at as date) = ?",
                [day],
            ).df()
