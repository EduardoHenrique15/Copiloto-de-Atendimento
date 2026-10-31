"""Treino, calibração, limiar e relatório do modelo de risco, de ponta a ponta.

Toda métrica publicada sobre o modelo de risco sai daqui (via scripts/train_risk.py).
"""

import json
from dataclasses import asdict
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import precision_recall_curve  # noqa: E402

from copiloto.ds.risk.calibration import (  # noqa: E402
    Calibrator,
    brier,
    reliability_table,
)
from copiloto.ds.risk.evaluate import bootstrap_diff, classification_metrics  # noqa: E402
from copiloto.ds.risk.explain import explain_order, global_importance, shap_values  # noqa: E402
from copiloto.ds.risk.features import FEATURES, TARGET, check_no_leakage  # noqa: E402
from copiloto.ds.risk.models import BaselineRule, LightGBMModel, LogisticModel  # noqa: E402
from copiloto.ds.risk.split import temporal_split  # noqa: E402
from copiloto.ds.risk.threshold import (  # noqa: E402
    CostAssumptions,
    best_threshold,
    sensitivity,
    value_at_threshold,
    value_curve,
)

SHAP_SAMPLE = 3000
SEED = 42


def choose_calibration(scores: np.ndarray, y: np.ndarray, times: pd.Series) -> dict:
    """Escolhe entre sem calibração, isotônica e Platt sem olhar o teste.

    Ajusta cada método na primeira metade (temporal) da validação e compara o
    Brier na segunda metade. O vencedor é reajustado na validação inteira.
    """
    order = np.argsort(times.to_numpy(), kind="stable")
    half = len(order) // 2
    fit_idx, check_idx = order[:half], order[half:]
    results = {}
    for method in ("none", "isotonic", "platt"):
        cal = Calibrator(method).fit(scores[fit_idx], y[fit_idx])
        results[method] = brier(y[check_idx], cal.transform(scores[check_idx]))
    chosen = min(results, key=results.get)
    return {"chosen": chosen, "brier_second_half_val": results}


def run_pipeline(
    df: pd.DataFrame,
    assumptions: CostAssumptions,
    figures_dir: Path,
    results_path: Path,
    model_path: Path | None = None,
) -> dict:
    """Roda tudo e devolve o relatório (também gravado em JSON)."""
    check_no_leakage(df)
    split = temporal_split(df)
    y_tr, y_val, y_te = (
        s[TARGET].astype(int).to_numpy() for s in (split.train, split.val, split.test)
    )

    # 1. Modelos
    baseline = BaselineRule().fit(split.train)
    logistic = LogisticModel().fit(split.train)
    lgbm = LightGBMModel().fit(split.train, split.val)
    raw = {
        name: (m.predict_proba(split.val), m.predict_proba(split.test))
        for name, m in (("baseline", baseline), ("logistic", logistic), ("lightgbm", lgbm))
    }

    # 2. Calibração do LightGBM (ajustada só na validação)
    cal_choice = choose_calibration(raw["lightgbm"][0], y_val, split.val["feature_cutoff_at"])
    calibrator = Calibrator(cal_choice["chosen"]).fit(raw["lightgbm"][0], y_val)
    p_val = calibrator.transform(raw["lightgbm"][0])
    p_test = calibrator.transform(raw["lightgbm"][1])

    test_metrics = {name: classification_metrics(y_te, p[1]) for name, p in raw.items()}
    test_metrics["lightgbm_calibrated"] = classification_metrics(y_te, p_test)
    val_metrics = {name: classification_metrics(y_val, p[0]) for name, p in raw.items()}

    comparisons = {
        "lightgbm_vs_baseline_pr_auc": bootstrap_diff(y_te, raw["lightgbm"][1], raw["baseline"][1]),
        "lightgbm_vs_logistic_pr_auc": bootstrap_diff(y_te, raw["lightgbm"][1], raw["logistic"][1]),
    }

    # 3. Limiar escolhido na validação, aplicado no teste
    chosen = best_threshold(y_val, p_val, assumptions)
    t = chosen["threshold"]
    policies_test = {
        "modelo_no_limiar": value_at_threshold(y_te, p_test, t, assumptions),
        "contatar_atrasados": value_at_threshold(
            y_te, split.test["is_late"].astype(float).to_numpy(), 0.5, assumptions
        ),
        "contatar_todos": value_at_threshold(y_te, np.ones_like(p_test), 0.5, assumptions),
        "nao_contatar": value_at_threshold(y_te, np.zeros_like(p_test), 0.5, assumptions),
    }
    sens = sensitivity(
        y_val, p_val, contact_costs=[1, 2, 5], negative_costs=[15, 30, 60], effects=[0.1, 0.2, 0.4]
    )

    # 4. SHAP global e 3 pedidos de exemplo (alto, médio e baixo risco) do teste
    sample = split.test.sample(min(SHAP_SAMPLE, len(split.test)), random_state=SEED)
    values, base_value = shap_values(lgbm, sample)
    sample_p = calibrator.transform(lgbm.predict_proba(sample))
    ranked = sample.index[np.argsort(sample_p)]
    picks = {"alto": ranked[-1], "medio": ranked[len(ranked) // 2], "baixo": ranked[0]}
    features_view = lgbm.transform(sample)
    examples = {
        level: {
            "order_id": str(sample.loc[idx, "order_id"]),
            "probability": float(sample_p[sample.index.get_loc(idx)]),
            "is_negative": bool(sample.loc[idx, TARGET]),
            "reasons": explain_order(values, features_view, idx),
        }
        for level, idx in picks.items()
    }

    report = {
        "features": FEATURES,
        "split": split.summary(),
        "lightgbm_best_iteration": lgbm.best_iteration,
        "calibration": cal_choice,
        "metrics_val": val_metrics,
        "metrics_test": test_metrics,
        "comparisons_test": comparisons,
        "assumptions": asdict(assumptions),
        "breakeven_probability": assumptions.breakeven_probability(),
        "threshold_val": chosen,
        "policies_test": policies_test,
        "sensitivity_val": sens,
        "shap_base_value_logodds": base_value,
        "shap_global": global_importance(values),
        "shap_examples": examples,
        "reliability_test": {
            "lightgbm_raw": reliability_table(y_te, raw["lightgbm"][1]),
            "lightgbm_calibrated": reliability_table(y_te, p_test),
        },
    }

    _plot_all(figures_dir, y_te, raw, p_test, y_val, p_val, assumptions, t, report)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    if model_path is not None:
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "model": lgbm,
                "calibrator": calibrator,
                "threshold": t,
                "assumptions": assumptions,
                "features": FEATURES,
                "trained_until": report["split"]["val_start"],
            },
            model_path,
        )
    return report


def _plot_all(figures_dir, y_te, raw, p_test, y_val, p_val, assumptions, t, report) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for name, (_, p) in raw.items():
        prec, rec, _ = precision_recall_curve(y_te, p)
        ax.plot(rec, prec, label=f"{name} (PR-AUC {report['metrics_test'][name]['pr_auc']:.3f})")
    ax.axhline(y_te.mean(), color="gray", linestyle="--", label="taxa base")
    ax.set(xlabel="Recall", ylabel="Precisão", title="Curva precisão-recall (teste)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "pr_curve.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5, 5))
    for label, rows in report["reliability_test"].items():
        ax.plot([r["predicted"] for r in rows], [r["observed"] for r in rows], "o-", label=label)
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", label="perfeito")
    ax.set(xlabel="Probabilidade prevista", ylabel="Taxa observada", title="Confiabilidade (teste)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "reliability.png", dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4.5))
    for label, y, p in (("validação", y_val, p_val), ("teste", y_te, p_test)):
        curve = value_curve(y, p, assumptions)
        ax.plot([r["threshold"] for r in curve], [r["value_brl"] for r in curve], label=label)
    ax.axvline(t, color="black", linestyle=":", label=f"limiar escolhido {t:.2f}")
    ax.axvline(
        assumptions.breakeven_probability(),
        color="gray",
        linestyle="--",
        label="ponto de equilíbrio",
    )
    ax.set(
        xlabel="Limiar", ylabel="Valor líquido (R$)", title="Valor do contato proativo por limiar"
    )
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "value_curve.png", dpi=120)
    plt.close(fig)

    top = report["shap_global"][::-1]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh([r["feature"] for r in top], [r["mean_abs_shap"] for r in top])
    ax.set(xlabel="Média de |SHAP| (log-odds)", title="Importância global (SHAP)")
    fig.tight_layout()
    fig.savefig(figures_dir / "shap_global.png", dpi=120)
    plt.close(fig)
