"""Relatório de impacto em reais: só números dos JSON gerados pelos scripts, mais premissas
explícitas. Nenhum valor é digitado à mão."""

from datetime import date


def _brl(v: float) -> str:
    """Reais: inteiro quando o valor é grande, com centavos quando é pequeno."""
    digits = 2 if abs(v) < 100 and v != int(v) else 0
    text = f"{abs(v):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{'−' if v < 0 else ''}R$ {text}"


def _pct(v: float, digits: int = 1) -> str:
    return f"{v:.{digits}%}".replace(".", ",")


def _num(v: float, digits: int = 0) -> str:
    return f"{v:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def compute(risk: dict, causal: dict, ab: dict, triage: dict, copilot: dict) -> dict:
    """Junta os números e faz as contas derivadas (todas aqui, testadas)."""
    premise = risk["assumptions"]
    att = causal["estimates"]["ipw_att"]
    ci = causal["bootstrap"]["ipw_att"]
    extra_negatives = att * causal["n_late"]
    test = risk["split"]["test"]
    test_days = (date.fromisoformat(test["end"]) - date.fromisoformat(test["start"])).days
    policies = risk["policies_test"]
    model = policies["modelo_no_limiar"]
    zs = triage["zero_shot"]
    return {
        "premise": premise,
        "causal": {
            "n_orders": causal["n_orders"],
            "n_late": causal["n_late"],
            "att": att,
            "att_low": ci["ci_low"],
            "att_high": ci["ci_high"],
            "per_1000_late": att * 1000,
            "extra_negatives": extra_negatives,
            "extra_negatives_low": ci["ci_low"] * causal["n_late"],
            "extra_negatives_high": ci["ci_high"] * causal["n_late"],
            "cost_brl": extra_negatives * premise["negative_review_cost_brl"],
        },
        "risk": {
            "test_days": test_days,
            "test_orders": test["n"],
            "policies": policies,
            "value_per_30_days": model["value_brl"] / test_days * 30,
        },
        "ab": {
            "daily": ab["pool"]["daily_eligible"],
            "plan": {round(p["relative_reduction"], 2): p for p in ab["plan"]},
        },
        "triage": {
            "accuracy": zs["quality"]["accuracy"],
            "coverage": zs["routing"]["coverage"],
            "accuracy_auto": zs["routing"]["accuracy_auto"],
            "cost_per_1000": zs["cost_per_1000_brl"],
        },
        "copilot": {
            "version": copilot["draft_prompt"],
            "citation": copilot["checks"]["citation"]["rate"],
            "action": copilot["checks"]["action"]["rate"],
            "cost_per_1000": copilot["cost"].get("draft_per_1000_brl"),
        },
    }


def render(n: dict) -> str:
    p, c, r, a, t, cp = n["premise"], n["causal"], n["risk"], n["ab"], n["triage"], n["copilot"]
    pol = r["policies"]
    rows = [
        ("Modelo no limiar", "modelo_no_limiar"),
        ("Contatar todo pedido atrasado", "contatar_atrasados"),
        ("Contatar todos", "contatar_todos"),
        ("Não contatar ninguém", "nao_contatar"),
    ]
    lines = [
        "# Relatório de impacto",
        "",
        "Gerado por `scripts/impact_report.py` a partir de `eval/results/`. Não edite à mão.",
        "",
        "Os valores em reais dependem de **premissas** (abaixo), que não foram medidas. A base é "
        "a Olist de 2016 a 2018, e as políticas e os custos da loja são fictícios.",
        "",
        "## Premissas",
        "",
        "| Premissa | Valor | Origem |",
        "| --- | ---: | --- |",
        f"| Custo de uma avaliação negativa | {_brl(p['negative_review_cost_brl'])} | "
        "Premissa (ADR 0005) |",
        f"| Custo de um contato proativo | {_brl(p['contact_cost_brl'])} | Premissa (ADR 0005) |",
        f"| Avaliações negativas evitadas pelo contato | {_pct(p['contact_effect'], 0)} | "
        "Premissa; é o que o teste A/B mediria |",
        "",
        "## 1. Quanto o atraso custa",
        "",
        f"- Efeito causal do atraso (IPW, ATT): **+{_num(c['att'] * 100, 1)} pontos percentuais** "
        f"na chance de nota 1 ou 2 (IC 95% de {_num(c['att_low'] * 100, 1)} a "
        f"{_num(c['att_high'] * 100, 1)}).",
        f"- São **{_num(c['per_1000_late'])} avaliações negativas a mais a cada 1.000 pedidos "
        "atrasados**.",
        f"- Na base: {_num(c['n_late'])} pedidos atrasados, de {_num(c['n_orders'])} avaliados, "
        f"geraram cerca de **{_num(c['extra_negatives'])} negativas a mais** (IC de "
        f"{_num(c['extra_negatives_low'])} a {_num(c['extra_negatives_high'])}).",
        f"- Com a premissa de {_brl(p['negative_review_cost_brl'])} por negativa: cerca de "
        f"**{_brl(c['cost_brl'])}** no período inteiro da base.",
        "",
        "## 2. Contato proativo com o modelo de risco",
        "",
        f"Período de teste: {r['test_days']} dias, {_num(r['test_orders'])} pedidos entregues. "
        "Valor líquido = negativas evitadas × custo da negativa − contatos × custo do contato.",
        "",
        "| Política | Contatos | Negativas alcançadas | Precisão | Valor líquido |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for label, key in rows:
        v = pol[key]
        lines.append(
            f"| {label} | {_num(v['contacts'])} | {_num(v['negatives_reached'])} | "
            f"{_pct(v['precision'])} | {_brl(v['value_brl'])} |"
        )
    lines += [
        "",
        f"- O modelo gera cerca de **{_brl(r['value_per_30_days'])} a cada 30 dias** no volume "
        "da base, contra quase zero da regra simples. Contatar todos dá prejuízo.",
        "- O ganho depende inteiramente do efeito do contato, que é premissa. Por isso, o "
        "próximo passo é o teste A/B, e não escalar o contato.",
        "",
        "## 3. Quanto tempo o teste A/B leva",
        "",
        f"Com {_num(a['daily'], 1)} pedidos elegíveis por dia:",
        "",
        "| Queda que o teste detecta | Pedidos por grupo | Duração |",
        "| --- | ---: | ---: |",
    ]
    for red, plan in sorted(a["plan"].items()):
        lines.append(
            f"| {_pct(red, 0)} | {_num(plan['n_per_group'])} | {_num(plan['days'])} dias |"
        )
    lines += [
        "",
        "## 4. Atendimento: triagem e copiloto",
        "",
        f"- **Triagem (zero-shot, teste):** acurácia de {_pct(t['accuracy'])} contra rótulos de "
        f"referência (feitos com apoio de IA, ADR 0013). {_pct(t['coverage'], 0)} dos tickets são "
        f"classificados sozinhos, com {_pct(t['accuracy_auto'])} de acerto. Custo de "
        f"referência: {_brl(t['cost_per_1000'])} por 1.000 tickets.",
    ]
    cost = "n/d" if cp["cost_per_1000"] is None else _brl(cp["cost_per_1000"])
    lines += [
        f"- **Copiloto ({cp['version']}, 60 casos fictícios):** cita a política esperada em "
        f"{_pct(cp['citation'])} e sugere uma ação aceita em {_pct(cp['action'])}. Custo de "
        f"referência: {cost} por 1.000 rascunhos.",
        "- O ganho em tempo de atendimento não foi medido: não há dados de tempo por ticket na "
        "base.",
        "",
    ]
    return "\n".join(lines)
