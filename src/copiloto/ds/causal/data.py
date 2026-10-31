"""Dados da análise causal: tratamento, resultados e confundidores."""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

TREATMENT = "is_late"
OUTCOME = "is_negative"
SCORE = "review_score"

# Tudo o que influencia ao mesmo tempo o atraso e a nota, e é conhecido antes do envio.
# Variáveis posteriores ao atraso (dias até a entrega, data de entrega) ficam de fora:
# controlar por elas bloquearia parte do próprio efeito.
NUMERIC_CONFOUNDERS = [
    "promised_days",
    "distance_km",
    "n_items",
    "n_sellers",
    "items_price",
    "freight_value",
    "freight_ratio",
    "max_installments",
    "seller_prior_orders",
    "seller_prior_avg_score",
    "seller_prior_late_rate",
    "purchase_month_index",
]
CATEGORICAL_CONFOUNDERS = ["customer_state", "seller_state", "main_category", "main_payment_type"]
BOOLEAN_CONFOUNDERS = ["same_state"]
CONFOUNDERS = NUMERIC_CONFOUNDERS + BOOLEAN_CONFOUNDERS + CATEGORICAL_CONFOUNDERS


def load_causal_frame(duckdb_path: Path) -> pd.DataFrame:
    """Lê `marts.fct_orders_causal` e cria o índice do mês da compra (tendência no tempo)."""
    with duckdb.connect(str(duckdb_path), read_only=True) as con:
        df = con.execute("select * from marts.fct_orders_causal").df()
    return prepare(df)


def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Tipos uniformes e colunas derivadas usadas pela análise."""
    df = df.copy()
    month = pd.to_datetime(df["purchase_month"])
    df["purchase_month_index"] = (month.dt.year - month.dt.year.min()) * 12 + month.dt.month
    df[TREATMENT] = df[TREATMENT].astype(bool)
    df[OUTCOME] = df[OUTCOME].astype(bool)
    return df


def design_matrix(df: pd.DataFrame, min_count: int = 200) -> pd.DataFrame:
    """Matriz numérica dos confundidores.

    Numéricas ausentes: mediana + indicador de ausência. Categorias raras (menos
    de `min_count` pedidos) viram "outros", para a propensão não sobreajustar.
    """
    parts = []
    for col in NUMERIC_CONFOUNDERS:
        x = pd.to_numeric(df[col], errors="coerce").astype(float)
        if x.isna().any():
            parts.append(x.isna().astype(float).rename(f"{col}__missing"))
        parts.append(x.fillna(x.median()).rename(col))
    for col in BOOLEAN_CONFOUNDERS:
        parts.append(df[col].astype(float).fillna(0).rename(col))
    for col in CATEGORICAL_CONFOUNDERS:
        x = df[col].astype("object").where(df[col].notna(), "missing").astype(str)
        counts = x.value_counts()
        x = x.where(x.map(counts) >= min_count, "outros")
        parts.append(pd.get_dummies(x, prefix=col, drop_first=True, dtype=float))
    out = pd.concat(parts, axis=1)
    out.index = df.index
    return out.loc[:, out.std() > 0]


def as_arrays(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Tratamento e resultado como vetores 0/1."""
    return df[TREATMENT].to_numpy(dtype=int), df[OUTCOME].to_numpy(dtype=int)
