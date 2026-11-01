"""Relatório markdown da avaliação do copiloto."""

from copiloto.ai.eval.judge import CRITERIA

CHECK_NAMES = {
    "citation": "Citação de uma política esperada",
    "action": "Ação entre as aceitas",
    "needs_human": "Envio para humano como esperado",
    "injection_flagged": "Injection detectada pelo guardrail",
}


def _pct(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.1%}"


def _num(value: float | None) -> str:
    return "n/d" if value is None else f"{value:.2f}"


def render(summary: dict) -> str:
    lines = [
        "# Copiloto: avaliação",
        "",
        "Gerado por `scripts/evaluate_copilot.py`. Não edite à mão.",
        "",
        f"Casos: {summary['n_cases']} (fictícios, `eval/copilot_cases.yaml`). "
        f"Prompt do rascunho: `{summary['draft_prompt']}`. Prompt do juiz: "
        f"`{summary.get('judge_prompt') or 'n/d'}`. Modelo: `{summary.get('model') or 'n/d'}`.",
        "",
        "## Verificações automáticas (sem LLM)",
        "",
        "| Verificação | n | Acerto |",
        "| --- | ---: | ---: |",
    ]
    for key, value in summary["checks"].items():
        lines.append(f"| {CHECK_NAMES[key]} | {value['n']} | {_pct(value['rate'])} |")
    g = summary["guardrails"]
    lines += [
        "",
        f"Guardrails: {g['any_rate']:.1%} dos rascunhos tiveram ao menos um evento; "
        f"{g['fallback_rate']:.1%} tiveram a resposta trocada pelo texto de encaminhamento.",
        "",
        "| Evento | Rascunhos |",
        "| --- | ---: |",
    ]
    for flag, count in g["by_flag"].items():
        lines.append(f"| {flag} | {count} |")
    c = summary["cost"]
    lines += [
        "",
        f"Custo de referência (preço pago): rascunho R$ {_num(c.get('draft_per_1000_brl'))} "
        f"por 1.000; juiz R$ {_num(c.get('judge_per_1000_brl'))} por 1.000. "
        f"Latência do rascunho: p50 {c['draft_p50_ms']:.0f} ms, p95 {c['draft_p95_ms']:.0f} ms.",
    ]
    judge = summary.get("judge")
    if judge:
        lines += [
            "",
            "## Juiz LLM (rubrica fixa)",
            "",
            f"Rascunhos julgados: {judge['n']} (falhas de formato: {judge['failures']}).",
            "",
            "| Critério | Aprovação |",
            "| --- | ---: |",
        ]
        for key in CRITERIA:
            lines.append(f"| {key} | {_pct(judge['pass_rate'][key])} |")
        lines.append(f"| todos os 5 | {_pct(judge['all_pass_rate'])} |")
    agreement = summary.get("agreement")
    if agreement:
        rule = agreement["rule"]
        verdict = "aceitável" if agreement["acceptable"] else "NÃO aceitável"
        lines += [
            "",
            "## Concordância juiz × avaliação humana",
            "",
            f"Rascunhos avaliados pelos dois: {agreement['n_cases']}. Concordância geral "
            f"{_pct(agreement['overall_agreement'])}, kappa {_num(agreement['overall_kappa'])}. "
            f"Regra (ADR 0011): concordância de pelo menos {rule['min_agreement']:.0%} e kappa "
            f"de pelo menos {rule['min_kappa']:.2f}. Resultado: **{verdict}**.",
            "",
            "| Critério | Concordância | Kappa | Aprovação humana | Aprovação do juiz |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
        for key, v in agreement["per_criterion"].items():
            lines.append(
                f"| {key} | {_pct(v['agreement'])} | {_num(v['kappa'])} | "
                f"{_pct(v['human_pass_rate'])} | {_pct(v['judge_pass_rate'])} |"
            )
        if not agreement["acceptable"]:
            lines += [
                "",
                "Como a concordância não atingiu a regra, os números do juiz acima não "
                "devem ser usados como medida de qualidade.",
            ]
    lines.append("")
    return "\n".join(lines)
