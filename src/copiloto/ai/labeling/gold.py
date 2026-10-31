"""Conjunto ouro: amostra, armazenamento dos rótulos humanos e concordância."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from copiloto.ai.labeling.sampling import stratified_sample
from copiloto.ai.taxonomy import CATEGORY_KEYS

LABEL_COLUMNS = ["complaint_id", "round", "label", "multiple_problems", "labeled_at", "labeler"]
REPEAT_WAIT = timedelta(days=7)


def make_gold_sample(
    complaints: pd.DataFrame,
    exclude: set[str],
    n: int = 300,
    n_val: int = 100,
    n_repeat: int = 50,
    seed: int = 2024,
) -> pd.DataFrame:
    """Sorteia o conjunto ouro (estratificado por nota e semestre).

    `split`: os primeiros `n_val` são validação; o resto, teste.
    `repeat`: `n_repeat` itens rotulados de novo depois de 7 dias (kappa do rotulador).
    """
    sample = stratified_sample(complaints, n, seed=seed, exclude=exclude)
    out = pd.DataFrame({"complaint_id": sample["complaint_id"]})
    out["split"] = np.where(np.arange(len(out)) < n_val, "val", "test")
    rng = np.random.default_rng(seed)
    repeat_idx = rng.choice(len(out), size=n_repeat, replace=False)
    out["repeat"] = False
    out.loc[repeat_idx, "repeat"] = True
    out["order"] = np.arange(len(out))
    return out


@dataclass
class GoldStore:
    """Rótulos humanos em CSV (só ids e rótulos, nunca o texto)."""

    path: Path

    def load(self) -> pd.DataFrame:
        if not self.path.exists():
            return pd.DataFrame(columns=LABEL_COLUMNS)
        return pd.read_csv(self.path, dtype={"complaint_id": str}, parse_dates=["labeled_at"])

    def save_label(
        self,
        complaint_id: str,
        round_: int,
        label: str,
        multiple_problems: bool,
        labeler: str = "eduardo",
        now: datetime | None = None,
    ) -> None:
        """Grava (ou substitui) o rótulo de um item numa rodada."""
        if label not in CATEGORY_KEYS:
            raise ValueError(f"Rótulo desconhecido: {label}")
        if round_ not in (1, 2):
            raise ValueError("Rodada precisa ser 1 ou 2.")
        labels = self.load()
        same = (labels["complaint_id"] == complaint_id) & (labels["round"] == round_)
        row = {
            "complaint_id": complaint_id,
            "round": round_,
            "label": label,
            "multiple_problems": bool(multiple_problems),
            "labeled_at": (now or datetime.now(UTC)).replace(microsecond=0),
            "labeler": labeler,
        }
        labels = pd.concat([labels[~same], pd.DataFrame([row])], ignore_index=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        labels.sort_values(["round", "labeled_at"]).to_csv(self.path, index=False)

    def remove_label(self, complaint_id: str, round_: int) -> None:
        """Desfaz um rótulo."""
        labels = self.load()
        keep = ~((labels["complaint_id"] == complaint_id) & (labels["round"] == round_))
        labels[keep].to_csv(self.path, index=False)


def pending(
    sample: pd.DataFrame, labels: pd.DataFrame, round_: int, now: datetime | None = None
) -> list[str]:
    """Ids que faltam rotular na rodada, na ordem da amostra.

    Rodada 2 só inclui itens de repetição cujo rótulo da rodada 1 tem 7 dias ou mais.
    """
    done = set(labels.loc[labels["round"] == round_, "complaint_id"])
    if round_ == 1:
        todo = sample.sort_values("order")["complaint_id"]
        return [c for c in todo if c not in done]
    now = now or datetime.now(UTC)
    first = labels[labels["round"] == 1].set_index("complaint_id")["labeled_at"]
    ready = []
    for cid in sample.loc[sample["repeat"], "complaint_id"]:
        if cid in done or cid not in first.index:
            continue
        labeled_at = pd.Timestamp(first[cid])
        labeled_at = labeled_at.tz_localize(UTC) if labeled_at.tzinfo is None else labeled_at
        if now - labeled_at.to_pydatetime() >= REPEAT_WAIT:
            ready.append(cid)
    return ready


def self_agreement(labels: pd.DataFrame) -> dict:
    """Kappa de Cohen entre a rodada 1 e a rodada 2 do mesmo rotulador."""
    r1 = labels[labels["round"] == 1].set_index("complaint_id")["label"]
    r2 = labels[labels["round"] == 2].set_index("complaint_id")["label"]
    common = r1.index.intersection(r2.index)
    if len(common) == 0:
        raise ValueError("Nenhum item rotulado nas duas rodadas.")
    a, b = r1.loc[common], r2.loc[common]
    disagreements = [
        {"complaint_id": c, "round_1": a[c], "round_2": b[c]} for c in common if a[c] != b[c]
    ]
    return {
        "n": int(len(common)),
        "kappa": float(cohen_kappa_score(a, b, labels=list(CATEGORY_KEYS))),
        "raw_agreement": float((a == b).mean()),
        "disagreements": disagreements,
    }
