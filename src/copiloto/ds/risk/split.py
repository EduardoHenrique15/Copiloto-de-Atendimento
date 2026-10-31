"""Divisão temporal em treino, validação e teste."""

from dataclasses import dataclass

import pandas as pd

TIME_COL = "feature_cutoff_at"


@dataclass(frozen=True)
class TemporalSplit:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame
    val_start: pd.Timestamp
    test_start: pd.Timestamp
    dropped_unlabeled: int

    def summary(self) -> dict[str, object]:
        """Tamanhos, períodos e taxa do alvo de cada parte."""
        out: dict[str, object] = {
            "val_start": str(self.val_start.date()),
            "test_start": str(self.test_start.date()),
            "dropped_unlabeled": self.dropped_unlabeled,
        }
        for name, part in (("train", self.train), ("val", self.val), ("test", self.test)):
            out[name] = {
                "n": len(part),
                "start": str(part[TIME_COL].min().date()),
                "end": str(part[TIME_COL].max().date()),
                "negative_rate": float(part["is_negative"].mean()),
            }
        return out


def temporal_split(
    df: pd.DataFrame, val_frac: float = 0.15, test_frac: float = 0.15
) -> TemporalSplit:
    """Divide pela data de entrega: o passado treina, o futuro avalia.

    Além da ordem temporal, cada parte só usa pedidos cujo rótulo (avaliação)
    já existia antes do início da parte seguinte. Na vida real, quem treina o
    modelo no dia `val_start` não conhece avaliações feitas depois desse dia.
    """
    if not 0 < val_frac < 1 or not 0 < test_frac < 1 or val_frac + test_frac >= 1:
        raise ValueError("Frações inválidas.")
    times = df[TIME_COL]
    val_start = times.quantile(1 - val_frac - test_frac)
    test_start = times.quantile(1 - test_frac)

    train_all = df[times < val_start]
    val_all = df[(times >= val_start) & (times < test_start)]
    train = train_all[train_all["review_created_at"] < val_start]
    val = val_all[val_all["review_created_at"] < test_start]
    test = df[times >= test_start]
    dropped = (len(train_all) - len(train)) + (len(val_all) - len(val))
    return TemporalSplit(train, val, test, val_start, test_start, dropped)
