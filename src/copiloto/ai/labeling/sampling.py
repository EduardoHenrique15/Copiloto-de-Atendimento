"""Amostragem estratificada das reclamações para rotulagem."""

from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

SEED = 42


def load_complaints(duckdb_path: Path) -> pd.DataFrame:
    """Lê `marts.fct_complaints` (comentários com nota até 3)."""
    with duckdb.connect(str(duckdb_path), read_only=True) as con:
        return con.execute("select * from marts.fct_complaints order by complaint_id").df()


def add_strata(df: pd.DataFrame) -> pd.DataFrame:
    """Estrato = nota x semestre da avaliação (ex.: "1|2017S2")."""
    out = df.copy()
    created = pd.to_datetime(out["review_created_at"])
    semester = created.dt.year.astype(str) + "S" + np.where(created.dt.month <= 6, "1", "2")
    out["stratum"] = out["review_score"].astype(str) + "|" + semester
    return out


def allocate(sizes: pd.Series, n: int) -> pd.Series:
    """Quantos itens tirar de cada estrato, proporcional ao tamanho
    (método dos maiores restos, para somar exatamente `n`)."""
    if n > sizes.sum():
        raise ValueError("Amostra maior que a população.")
    exact = sizes / sizes.sum() * n
    base = np.floor(exact).astype(int)
    remainder = (exact - base).sort_values(ascending=False, kind="stable")
    base[remainder.index[: n - base.sum()]] += 1
    return base


def stratified_sample(
    df: pd.DataFrame, n: int, seed: int = SEED, exclude: set[str] | None = None
) -> pd.DataFrame:
    """Amostra estratificada por nota e semestre, reprodutível pela semente.

    `exclude` recebe ids de reclamações que não podem ser sorteadas de novo
    (por exemplo, as usadas para definir a taxonomia).
    """
    pool = add_strata(df)
    if exclude:
        pool = pool[~pool["complaint_id"].isin(exclude)]
    counts = allocate(pool["stratum"].value_counts().sort_index(), n)
    parts = [
        pool[pool["stratum"] == stratum].sample(k, random_state=seed)
        for stratum, k in counts.items()
        if k > 0
    ]
    sample = pd.concat(parts)
    # Embaralha para o rotulador não ver os estratos em sequência.
    return sample.sample(frac=1, random_state=seed).reset_index(drop=True)
