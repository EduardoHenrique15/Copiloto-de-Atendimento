"""Leitura dos conjuntos de triagem: prata (treino) e ouro (validação e teste)."""

from pathlib import Path

import pandas as pd

from copiloto.ai.labeling.gold import GoldStore
from copiloto.ai.labeling.sampling import load_complaints


def complaint_texts(complaints: pd.DataFrame) -> pd.Series:
    """Título entre colchetes + comentário, como o rotulador e o LLM viram."""
    title = complaints["comment_title"].fillna("")
    text = title.where(title == "", "[" + title + "] ") + complaints["comment_message"]
    return text.str.strip()


def with_texts(ids: pd.DataFrame, duckdb_path: Path) -> pd.DataFrame:
    complaints = load_complaints(duckdb_path)
    complaints["text"] = complaint_texts(complaints)
    return ids.merge(complaints[["complaint_id", "text"]], on="complaint_id", how="left")


def load_silver(labels_dir: Path, duckdb_path: Path) -> pd.DataFrame:
    """Conjunto prata com textos: complaint_id, label, multiple_problems, text."""
    silver = pd.read_csv(labels_dir / "silver.csv")
    return with_texts(silver, duckdb_path)


class GoldNotReadyError(RuntimeError):
    """O conjunto ouro da divisão pedida ainda não foi todo rotulado."""


def load_gold(labels_dir: Path, duckdb_path: Path, split: str) -> pd.DataFrame:
    """Rótulos humanos da rodada 1 para a divisão `val` ou `test`, com textos.

    Falha se faltar rótulo: avaliar com o ouro incompleto daria números enviesados.
    """
    sample = pd.read_csv(labels_dir / "gold_sample.csv")
    sample = sample[sample["split"] == split]
    labels = GoldStore(labels_dir / "gold.csv").load()
    labels = labels[labels["round"] == 1][["complaint_id", "label", "multiple_problems"]]
    merged = sample.merge(labels, on="complaint_id", how="left")
    missing = int(merged["label"].isna().sum())
    if missing:
        raise GoldNotReadyError(
            f"Faltam {missing} de {len(merged)} rótulos humanos na divisão '{split}'."
        )
    return with_texts(merged, duckdb_path)
