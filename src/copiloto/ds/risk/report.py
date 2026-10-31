"""Converte o relatório do pipeline de risco em markdown."""

FEATURE_LABELS = {
    "delay_days": "dias de atraso (negativo = adiantado)",
    "is_late": "atrasou",
    "delivery_days": "dias até a entrega",
    "promised_days": "prazo prometido (dias)",
    "seller_prior_avg_score": "nota média anterior do vendedor",
    "seller_prior_late_rate": "taxa de atraso anterior do vendedor",
    "seller_prior_orders": "pedidos anteriores do vendedor",
    "distance_km": "distância cliente-vendedor (km)",
}


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _int(x: int) -> str:
    return f"{x:,}".replace(",", ".")


LEVEL_LABELS = {"alto": "alto", "medio": "médio", "baixo": "baixo"}


def _brl(x: float) -> str:
    return f"R$ {x:,.0f}".replace(",", ".")


def render(report: dict) -> str:
    """Markdown com todos os números do relatório. Não deve ser editado à mão."""
    s = report["split"]
    a = report["assumptions"]
    lines = [
        "# Modelo de risco: resultados",
        "",
        "Gerado por `scripts/train_risk.py`. Não edite à mão: rode o script de novo.",
        "",
        "## Divisão temporal",
        "",
        "| Parte | Pedidos | Período (entrega) | Taxa negativa |",
        "| --- | ---: | --- | ---: |",
    ]
    for part in ("train", "val", "test"):
        p = s[part]
        lines.append(
            f"| {part} | {_int(p['n'])} | {p['start']} a {p['end']} | {_pct(p['negative_rate'])} |"
        )
    lines += [
        "",
        f"Pedidos descartados por o rótulo ainda não existir na data de corte: "
        f"{_int(s['dropped_unlabeled'])}.",
        "",
        "## Métricas no teste",
        "",
        "| Modelo | PR-AUC | ROC-AUC | Brier | ECE |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for name, m in report["metrics_test"].items():
        lines.append(
            f"| {name} | {m['pr_auc']:.3f} | {m['roc_auc']:.3f} | "
            f"{m['brier']:.4f} | {m['ece']:.4f} |"
        )
    base_rate = report["metrics_test"]["lightgbm"]["base_rate"]
    lines += ["", f"Taxa base no teste (PR-AUC de um modelo aleatório): {base_rate:.3f}.", ""]
    lines += ["### Diferenças de PR-AUC (bootstrap pareado, IC 95%)", ""]
    for name, c in report["comparisons_test"].items():
        lines.append(f"- {name}: {c['diff']:+.3f} (IC {c['ci_low']:+.3f} a {c['ci_high']:+.3f})")

    cal = report["calibration"]
    lines += [
        "",
        "## Calibração",
        "",
        f"Método escolhido: **{cal['chosen']}** (menor Brier na segunda metade da validação: "
        + ", ".join(f"{k} {v:.4f}" for k, v in cal["brier_second_half_val"].items())
        + ").",
        "",
        "![Confiabilidade](../figures/risk/reliability.png)",
        "",
        "## Limiar por custo",
        "",
        f"Premissas: contato custa {_brl(a['contact_cost_brl'])}, evitar uma avaliação "
        f"negativa vale {_brl(a['negative_review_cost_brl'])}, e o contato evita "
        f"{_pct(a['contact_effect'])} das negativas.",
        "",
        f"Ponto de equilíbrio teórico: p = {report['breakeven_probability']:.3f}. "
        f"Limiar escolhido na validação: **{report['threshold_val']['threshold']:.2f}**.",
        "",
        "Resultado das políticas no teste:",
        "",
        "| Política | Contatos | Negativas alcançadas | Precisão | Recall | Valor líquido |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, r in report["policies_test"].items():
        lines.append(
            f"| {name} | {_int(r['contacts'])} | {_int(r['negatives_reached'])} | "
            f"{_pct(r['precision'])} | {_pct(r['recall'])} | {_brl(r['value_brl'])} |"
        )
    lines += [
        "",
        "![Valor por limiar](../figures/risk/value_curve.png)",
        "",
        "### Sensibilidade às premissas (validação)",
        "",
        "| Custo contato | Valor da negativa | Efeito | Equilíbrio "
        "| Melhor limiar | Contatos | Valor |",
        "| ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in report["sensitivity_val"]:
        lines.append(
            f"| {_brl(r['contact_cost_brl'])} | {_brl(r['negative_review_cost_brl'])} | "
            f"{_pct(r['contact_effect'])} | {r['breakeven']:.2f} | {r['threshold']:.2f} | "
            f"{_int(r['contacts'])} | {_brl(r['value_brl'])} |"
        )
    lines += [
        "",
        "## Explicabilidade (SHAP)",
        "",
        "![SHAP global](../figures/risk/shap_global.png)",
        "",
        "| Feature | Média de \\|SHAP\\| |",
        "| --- | ---: |",
    ]
    for r in report["shap_global"]:
        label = FEATURE_LABELS.get(r["feature"], r["feature"])
        lines.append(f"| {label} | {r['mean_abs_shap']:.3f} |")
    lines += ["", "### Três pedidos de exemplo (teste)", ""]
    for level, ex in report["shap_examples"].items():
        outcome = "negativa" if ex["is_negative"] else "não negativa"
        lines += [
            f"**Risco {LEVEL_LABELS.get(level, level)}**: probabilidade {_pct(ex['probability'])}, "
            f"avaliação real {outcome}.",
            "",
        ]
        for r in ex["reasons"]:
            label = FEATURE_LABELS.get(r["feature"], r["feature"])
            lines.append(f"- {label} = {r['value']}: {r['direction']} o risco ({r['shap']:+.2f})")
        lines.append("")
    return "\n".join(lines)
