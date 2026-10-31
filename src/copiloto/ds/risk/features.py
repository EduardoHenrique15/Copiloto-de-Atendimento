"""Features do modelo de risco e proteção contra vazamento."""

from pathlib import Path

import duckdb
import pandas as pd

from copiloto.core.errors import CopilotoError

TARGET = "is_negative"

NUMERIC_FEATURES = [
    "promised_days",
    "delivery_days",
    "delay_days",
    "n_items",
    "n_products",
    "n_sellers",
    "items_price",
    "freight_value",
    "freight_ratio",
    "max_installments",
    "n_payment_types",
    "distance_km",
    "seller_prior_orders",
    "seller_prior_avg_score",
    "seller_prior_n_reviews",
    "seller_prior_late_rate",
    "seller_prior_n_delivered",
]
BOOLEAN_FEATURES = ["is_late", "same_state"]
CATEGORICAL_FEATURES = ["main_category", "main_payment_type", "customer_state", "seller_state"]
FEATURES = NUMERIC_FEATURES + BOOLEAN_FEATURES + CATEGORICAL_FEATURES

# Colunas que só existem depois da avaliação: nunca podem virar feature.
FORBIDDEN_FEATURES = {TARGET, "review_score", "review_created_at"}
FORBIDDEN_PREFIXES = ("review_",)

METADATA = ["order_id", "purchased_at", "feature_cutoff_at", "review_created_at", "seller_id"]


class LeakageError(CopilotoError):
    """Uma feature usa informação posterior ao momento da previsão."""


def check_feature_list(features: list[str]) -> None:
    """Falha se alguma feature for o alvo ou vier da avaliação."""
    bad = [f for f in features if f in FORBIDDEN_FEATURES or f.startswith(FORBIDDEN_PREFIXES)]
    if bad:
        raise LeakageError(f"Features proibidas (posteriores à entrega): {bad}")


def check_no_leakage(df: pd.DataFrame, features: list[str] = FEATURES) -> None:
    """Verifica a lista de features e a ordem das datas de cada pedido.

    A data de corte é a entrega (`feature_cutoff_at`). A compra precisa ser
    anterior ao corte, e o alvo (avaliação) é o único dado que pode ser posterior.
    """
    check_feature_list(features)
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise LeakageError(f"Features ausentes na tabela: {missing}")
    after_cutoff = df["purchased_at"] > df["feature_cutoff_at"]
    if after_cutoff.any():
        raise LeakageError(f"{int(after_cutoff.sum())} pedidos com compra depois do corte.")


def load_risk_frame(duckdb_path: Path) -> pd.DataFrame:
    """Lê `marts.fct_orders_risk` do DuckDB gerado pelo dbt."""
    with duckdb.connect(str(duckdb_path), read_only=True) as con:
        df = con.execute("select * from marts.fct_orders_risk").df()
    df[TARGET] = df[TARGET].astype(bool)
    return df


def to_model_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Seleciona as features com tipos uniformes (booleanos viram 0/1)."""
    out = df[FEATURES].copy()
    for col in NUMERIC_FEATURES:
        out[col] = pd.to_numeric(out[col], errors="coerce").astype("float64")
    for col in BOOLEAN_FEATURES:
        out[col] = out[col].astype("float64")
    for col in CATEGORICAL_FEATURES:
        out[col] = out[col].astype("object").where(out[col].notna(), "missing").astype(str)
    return out
