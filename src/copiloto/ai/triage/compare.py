"""Roda as abordagens no conjunto ouro e monta a comparação."""

import time
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pandas as pd

from copiloto.ai.triage.base import Triager
from copiloto.ai.triage.metrics import (
    choose_threshold,
    coverage_curve,
    latency,
    quality,
    robustness,
)
from copiloto.core.costs import LLMPrice, cost_per_thousand_brl

PRED_COLUMNS = ["complaint_id", "pred", "confidence", "latency_ms", "input_tokens", "output_tokens"]


def predict_split(
    triager: Triager,
    gold: pd.DataFrame,
    cache_path: Path,
    min_interval_s: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> pd.DataFrame:
    """Previsões para cada item do ouro, gravadas incrementalmente (retoma se cair)."""
    done = pd.read_csv(cache_path) if cache_path.exists() else pd.DataFrame(columns=PRED_COLUMNS)
    todo = gold[~gold["complaint_id"].isin(set(done["complaint_id"]))]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    for row in todo.itertuples():
        result = triager.predict(row.text)
        pd.DataFrame(
            [
                {
                    "complaint_id": row.complaint_id,
                    "pred": result.category,
                    "confidence": result.confidence,
                    "latency_ms": result.latency_ms,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                }
            ]
        ).to_csv(cache_path, mode="a", header=not cache_path.exists(), index=False)
        if min_interval_s and not result.cached:
            sleep(min_interval_s)
    preds = pd.read_csv(cache_path)
    return gold.merge(preds, on="complaint_id", how="inner")


def summarize(
    frame: pd.DataFrame,
    price: LLMPrice | None = None,
    cpu_brl_per_hour: float | None = None,
    target_accuracy: float = 0.85,
) -> dict:
    """Qualidade, latência, custo por 1.000 tickets, robustez e roteamento por confiança.

    Custo: abordagens com tokens usam o preço do LLM; as locais usam o tempo de CPU
    medido vezes o preço-hora de uma máquina (premissa documentada).
    """
    correct = (frame["label"] == frame["pred"]).to_numpy()
    tokens_in = float(frame["input_tokens"].mean())
    tokens_out = float(frame["output_tokens"].mean())
    if tokens_in or tokens_out:
        cost = cost_per_thousand_brl(tokens_in, tokens_out, price) if price else None
        cost_basis = "tokens x preço do LLM"
    else:
        mean_s = float(frame["latency_ms"].mean()) / 1000
        cost = mean_s * cpu_brl_per_hour / 3600 * 1000 if cpu_brl_per_hour else None
        cost_basis = "tempo de CPU x preço-hora da máquina"
    curve = coverage_curve(frame["confidence"].to_numpy(dtype=float), correct)
    return {
        "quality": quality(frame["label"].tolist(), frame["pred"].tolist()),
        "latency": latency(frame["latency_ms"].tolist()),
        "cost_per_1000_brl": cost,
        "cost_basis": cost_basis,
        "mean_tokens": {"input": tokens_in, "output": tokens_out},
        "robustness": robustness(frame),
        "coverage_curve": curve,
        "routing": choose_threshold(curve, target_accuracy),
        "target_accuracy": target_accuracy,
        "mean_confidence_correct": float(frame.loc[correct, "confidence"].mean())
        if correct.any()
        else None,
        "mean_confidence_wrong": float(frame.loc[~correct, "confidence"].mean())
        if (~correct).any()
        else None,
    }


def render(split: str, results: dict[str, dict]) -> str:
    """Tabela markdown da comparação."""
    lines = [
        f"# Triagem: comparação no ouro ({split})",
        "",
        "Gerado por `scripts/evaluate_triage.py`. Não edite à mão.",
        "",
        "| Abordagem | F1 macro | Acurácia | p50 | p95 | R$ / 1.000 tickets |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, r in results.items():
        q, lat = r["quality"], r["latency"]
        cost = "n/d" if r["cost_per_1000_brl"] is None else f"R$ {r['cost_per_1000_brl']:.2f}"
        lines.append(
            f"| {name} | {q['macro_f1']:.3f} | {q['accuracy']:.1%} | "
            f"{lat['p50_ms']:.0f} ms | {lat['p95_ms']:.0f} ms | {cost} |"
        )
    for name, r in results.items():
        q = r["quality"]
        lines += [
            "",
            f"## {name}",
            "",
            f"Base do custo: {r['cost_basis']}. "
            f"Roteamento: com confiança mínima {r['routing']['threshold']:.2f}, "
            f"{r['routing']['coverage']:.0%} dos tickets são classificados automaticamente, "
            f"com acurácia de {r['routing']['accuracy_auto']:.1%} "
            f"(meta {r['target_accuracy']:.0%}); o resto vai para revisão humana.",
            "",
            "| Categoria | Precisão | Recall | F1 | Suporte |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for cat, m in q["per_category"].items():
            lines.append(
                f"| {cat} | {m['precision']:.2f} | {m['recall']:.2f} | "
                f"{m['f1']:.2f} | {m['support']} |"
            )
        lines += ["", "| Fatia | n | Acurácia |", "| --- | ---: | ---: |"]
        for s, v in r["robustness"].items():
            acc = "n/d" if v["accuracy"] is None else f"{v['accuracy']:.1%}"
            lines.append(f"| {s} | {v['n']} | {acc} |")
        labels = q["confusion"]["labels"]
        short = [lab[:12] for lab in labels]
        lines += ["", "Matriz de confusão (linhas: humano; colunas: previsto):", ""]
        lines.append("| | " + " | ".join(short) + " |")
        lines.append("| --- |" + " ---: |" * len(labels))
        for lab, row in zip(short, q["confusion"]["matrix"], strict=True):
            lines.append(f"| {lab} | " + " | ".join(str(v) for v in row) + " |")
    lines.append("")
    return "\n".join(lines)


def agreement_with_gold(silver_like: pd.Series, gold: pd.Series) -> float:
    """Fração de concordância entre dois vetores de rótulos alinhados."""
    return float(np.mean(silver_like.to_numpy() == gold.to_numpy()))
