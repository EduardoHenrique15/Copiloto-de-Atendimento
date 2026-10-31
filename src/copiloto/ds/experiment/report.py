"""Markdown do desenho do teste A/B."""


def _pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def _int(x: float) -> str:
    return f"{round(x):,}".replace(",", ".")


def render(design: dict) -> str:
    """Markdown com os números do desenho. Não deve ser editado à mão."""
    pool = design["pool"]
    lines = [
        "# Teste A/B do contato proativo: números do desenho",
        "",
        "Gerado por `scripts/ab_design.py`. Não edite à mão: rode o script de novo.",
        "",
        "## População elegível (histórico, fora do período de treino do modelo)",
        "",
        f"- Pedidos de alto risco (probabilidade ≥ limiar do modelo): {_int(pool['n'])}, "
        f"de {pool['start']} a {pool['end']} ({pool['days']} dias)",
        f"- Volume diário médio: {pool['daily_eligible']:.1f} pedidos",
        f"- Taxa negativa nesse grupo (linha de base): {_pct(pool['baseline_negative_rate'])}",
        f"- Probabilidade média prevista: {_pct(pool['mean_probability'])}",
        "",
        "## Tamanho de amostra e duração (alfa 5% bilateral, poder 80%, 50/50)",
        "",
        "| Redução relativa mínima | Taxa no tratamento | Pedidos por grupo | Total | Dias |",
        "| ---: | ---: | ---: | ---: | ---: |",
    ]
    for r in design["plan"]:
        lines.append(
            f"| {_pct(r['relative_reduction'])} | {_pct(r['treated_rate'])} | "
            f"{_int(r['n_per_group'])} | {_int(r['n_total'])} | {_int(r['days'])} |"
        )
    a = design["assignment_check"]
    lines += [
        "",
        f"Sorteio determinístico (semente {a['seed']}): {_pct(a['share_treatment'])} dos pedidos "
        "elegíveis caem no tratamento.",
        "",
        "## Simulação com os dados históricos",
        "",
        "Cada simulação sorteia os grupos de novo e aplica um efeito conhecido no tratamento.",
        "",
        "| Efeito verdadeiro | Simulações | Pedidos | % significativo | Efeito médio estimado "
        "| Cobertura do IC 95% |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for s in design["simulations"]:
        lines.append(
            f"| {_pct(s['true_relative_reduction'])} | {s['n_sims']} | {_int(s['n_orders'])} | "
            f"{_pct(s['share_significant'])} | {_pct(-s['mean_estimated_relative_change'])} | "
            f"{_pct(s['ci_coverage'])} |"
        )
    lines += [
        "",
        'Com efeito 0%, "% significativo" é a taxa de falso positivo (esperado: perto de 5%). '
        "Com efeito maior que 0, é o poder com o tamanho histórico disponível.",
        "",
    ]
    return "\n".join(lines)
