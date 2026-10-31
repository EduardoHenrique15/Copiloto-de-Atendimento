"""Métricas da comparação: qualidade, latência, custo e robustez."""

import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, f1_score, precision_recall_fscore_support

from copiloto.ai.taxonomy import CATEGORY_KEYS

SHORT_TEXT_CHARS = 30
LONG_TEXT_CHARS = 300


def quality(y_true: list[str], y_pred: list[str]) -> dict:
    """F1 macro, acurácia, métricas por categoria e matriz de confusão."""
    labels = list(CATEGORY_KEYS)
    p, r, f, s = precision_recall_fscore_support(y_true, y_pred, labels=labels, zero_division=0)
    return {
        "n": len(y_true),
        "macro_f1": float(
            f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)
        ),
        "accuracy": float(np.mean(np.array(y_true) == np.array(y_pred))),
        "per_category": {
            lab: {
                "precision": float(p[i]),
                "recall": float(r[i]),
                "f1": float(f[i]),
                "support": int(s[i]),
            }
            for i, lab in enumerate(labels)
        },
        "confusion": {
            "labels": labels,
            "matrix": confusion_matrix(y_true, y_pred, labels=labels).tolist(),
        },
    }


def latency(latencies_ms: list[float]) -> dict:
    values = np.asarray(latencies_ms, dtype=float)
    return {
        "p50_ms": float(np.percentile(values, 50)),
        "p95_ms": float(np.percentile(values, 95)),
        "mean_ms": float(values.mean()),
    }


def robustness(frame: pd.DataFrame) -> dict:
    """Acurácia em fatias difíceis. `frame` tem text, label, pred e multiple_problems."""
    length = frame["text"].str.len()
    slices = {
        "curtos (<= 30 caracteres)": length <= SHORT_TEXT_CHARS,
        "longos (> 300 caracteres)": length > LONG_TEXT_CHARS,
        "mais de um problema": frame["multiple_problems"].astype(bool),
        "um problema só": ~frame["multiple_problems"].astype(bool),
    }
    out = {}
    for name, mask in slices.items():
        part = frame[mask]
        out[name] = {
            "n": int(len(part)),
            "accuracy": float((part["label"] == part["pred"]).mean()) if len(part) else None,
        }
    return out


def coverage_curve(confidence: np.ndarray, correct: np.ndarray) -> list[dict]:
    """Para cada limiar de confiança: fração classificada automaticamente e acurácia dela."""
    rows = []
    for t in np.round(np.arange(0.0, 1.0, 0.05), 2):
        auto = confidence >= t
        rows.append(
            {
                "threshold": float(t),
                "coverage": float(auto.mean()),
                "accuracy_auto": float(correct[auto].mean()) if auto.any() else None,
            }
        )
    return rows


def choose_threshold(curve: list[dict], target_accuracy: float) -> dict:
    """Menor limiar cuja acurácia automática atinge a meta (maximiza cobertura).
    Se nenhum atingir, devolve o de maior acurácia."""
    ok = [
        r for r in curve if r["accuracy_auto"] is not None and r["accuracy_auto"] >= target_accuracy
    ]
    if ok:
        return min(ok, key=lambda r: r["threshold"])
    valid = [r for r in curve if r["accuracy_auto"] is not None]
    return max(valid, key=lambda r: r["accuracy_auto"])
