"""Gráficos e markdown da análise causal."""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402


def _pp(x: float) -> str:
    """Pontos percentuais."""
    return f"{100 * x:+.1f} p.p."


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _int(x: float) -> str:
    return f"{round(x):,}".replace(",", ".")


def plot(report: dict, figures_dir: Path) -> None:
    """Histograma de propensão por grupo e gráfico de balanceamento (love plot)."""
    figures_dir.mkdir(parents=True, exist_ok=True)
    e, t = report["propensity"], report["treatment"]

    fig, ax = plt.subplots(figsize=(6, 4))
    bins = np.linspace(0, 1, 41)
    ax.hist(e[t == 0], bins=bins, alpha=0.6, density=True, label="no prazo")
    ax.hist(e[t == 1], bins=bins, alpha=0.6, density=True, label="atrasado")
    ax.set(xlabel="Propensão ao atraso", ylabel="Densidade", title="Sobreposição da propensão")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "propensity_overlap.png", dpi=120)
    plt.close(fig)

    table = report["balance_table"]
    names = sorted(table, key=lambda c: abs(table[c]["before"]))[-20:]
    fig, ax = plt.subplots(figsize=(6, 6))
    for method, marker in (("before", "o"), ("ipw", "s"), ("matching", "^")):
        ax.scatter([abs(table[c][method]) for c in names], names, marker=marker, label=method)
    ax.axvline(0.1, color="gray", linestyle="--")
    ax.set(xlabel="|SMD|", title="Balanceamento (20 covariáveis mais desbalanceadas)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figures_dir / "balance.png", dpi=120)
    plt.close(fig)


def serializable(report: dict) -> dict:
    """Remove os vetores grandes antes de gravar em JSON."""
    return {k: v for k, v in report.items() if k not in {"propensity", "treatment"}}


def save_json(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(serializable(report), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def render(report: dict) -> str:
    """Markdown com os números da análise causal. Não deve ser editado à mão."""
    est, ci, b = report["estimates"], report["bootstrap"], report["business"]
    ov, sens = report["overlap"], report["sensitivity"]
    lines = [
        "# Análise causal: resultados",
        "",
        "Gerado por `scripts/causal_analysis.py`. Não edite à mão: rode o script de novo.",
        "",
        "## Dados",
        "",
        f"- Pedidos entregues e avaliados: {_int(report['n_orders'])}",
        f"- Atrasados: {_int(report['n_late'])} ({_pct(report['late_rate'])})",
        f"- Taxa negativa: atrasados {_pct(report['negative_rate_late'])}, "
        f"no prazo {_pct(report['negative_rate_on_time'])}",
        f"- Covariáveis na propensão (após one-hot): {report['n_covariates']}",
        "",
        "## Efeito do atraso na chance de nota negativa",
        "",
        "| Estimador | Efeito | IC 95% (bootstrap) |",
        "| --- | ---: | --- |",
    ]
    rows = [
        ("Diferença ingênua", "naive"),
        ("IPW (ATT)", "ipw_att"),
        ("Pareamento (ATT)", "matching_att"),
        ("IPW (ATE)", "ipw_ate"),
    ]
    for label, key in rows:
        lines.append(
            f"| {label} | {_pp(est[key])} | {_pp(ci[key]['ci_low'])} a {_pp(ci[key]['ci_high'])} |"
        )
    lines += [
        "",
        f"Bootstrap com {ci['n_boot']} reamostras, reajustando a propensão em cada uma.",
        "",
        f"Sem atraso, os pedidos atrasados teriam taxa negativa estimada de "
        f"{_pct(est['ipw_att_control_mean'])} (IPW), contra {_pct(report['negative_rate_late'])} "
        "observada.",
        "",
        "## Efeito na nota média (1 a 5)",
        "",
        "| Estimador | Efeito |",
        "| --- | ---: |",
    ]
    for label, key in (
        ("Ingênuo", "naive"),
        ("IPW (ATT)", "ipw_att"),
        ("Pareamento", "matching_att"),
    ):
        lines.append(f"| {label} | {report['score_effect'][key]:+.2f} |")
    m = report["matching_details"]
    lines += [
        "",
        "## Sobreposição",
        "",
        f"- Propensão média: atrasados {ov['treated_mean_propensity']:.3f}, "
        f"no prazo {ov['control_mean_propensity']:.3f}",
        f"- Faixa comum: {ov['common_low']:.3f} a {ov['common_high']:.3f}; "
        f"fora dela: {_pct(ov['share_outside_common_support'])} dos pedidos",
        f"- Pedidos no limite de corte da propensão (0,01 ou 0,99): {_pct(ov['share_at_clip'])}",
        f"- Pareamento: {_int(m['n_treated_matched'])} atrasados pareados, "
        f"{_int(m['n_treated_dropped'])} descartados pelo caliper, "
        f"{_int(m['n_unique_controls'])} controles distintos usados",
        "",
        "![Sobreposição](figures/causal/propensity_overlap.png)",
        "",
        "## Balanceamento (|SMD| < 0,1 é bom)",
        "",
        "| Método | Maior \\|SMD\\| | Covariáveis acima de 0,1 |",
        "| --- | ---: | ---: |",
    ]
    for method, label in (("before", "Antes"), ("ipw", "IPW"), ("matching", "Pareamento")):
        s = report["balance"][method]
        lines.append(
            f"| {label} | {s['max_abs_smd']:.3f} | "
            f"{s['n_above_threshold']} de {s['n_covariates']} |"
        )
    lines += [
        "",
        "![Balanceamento](figures/causal/balance.png)",
        "",
        "## Sensibilidade a confundidor não observado",
        "",
        f"- Razão de risco (IPW): {sens['risk_ratio']:.2f} "
        f"(limite inferior do IC: {sens['risk_ratio_ci_low']:.2f})",
        f"- E-value: {sens['e_value']:.2f} (para o limite do IC: {sens['e_value_ci']:.2f})",
        "",
        "## Tradução em negócio",
        "",
        f"- Cada 1.000 pedidos atrasados geram **{b['extra_negatives_per_1000_late']:.0f}** "
        f"avaliações negativas a mais (IC 95%: {b['extra_negatives_per_1000_late_ci'][0]:.0f} "
        f"a {b['extra_negatives_per_1000_late_ci'][1]:.0f}).",
        f"- Com a premissa de R$ {b['negative_review_cost_brl']:.0f} por avaliação negativa: "
        f"R$ {_int(b['cost_per_1000_late_brl'])} a cada 1.000 pedidos atrasados.",
        f"- Na base inteira: {_int(b['late_orders_in_base'])} atrasados, cerca de "
        f"{_int(b['extra_negatives_in_base'])} negativas causadas pelo atraso.",
        "",
    ]
    return "\n".join(lines)
