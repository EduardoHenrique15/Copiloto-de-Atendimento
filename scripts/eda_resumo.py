"""Gera docs/eda-resumo.md com os números da análise exploratória.

Lê o DuckDB criado pelo dbt. Todo número citado no projeto sobre a base
vem deste script. Uso:

    python scripts/eda_resumo.py
    python scripts/eda_resumo.py --data-dir tests/data/olist --out caminho/saida.md
"""

import argparse
import os
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]

QUERIES: dict[str, str] = {
    "pedidos": "select count(*) from staging.stg_orders",
    "pedidos_entregues": (
        "select count(*) from staging.stg_orders "
        "where order_status = 'delivered' and delivered_customer_at is not null"
    ),
    "compra_min": "select min(purchased_at)::date from staging.stg_orders",
    "compra_max": "select max(purchased_at)::date from staging.stg_orders",
    "avaliacoes": "select count(*) from staging.stg_reviews",
    "pedidos_com_mais_de_uma_avaliacao": (
        "select count(*) from intermediate.int_order_reviews where n_reviews > 1"
    ),
    "avaliacoes_com_comentario": (
        "select count(*) from staging.stg_reviews where comment_message is not null"
    ),
    "taxa_sem_comentario": (
        "select avg(case when comment_message is null then 1.0 else 0.0 end) "
        "from staging.stg_reviews"
    ),
    "linhas_fct_orders_risk": "select count(*) from marts.fct_orders_risk",
    "taxa_negativa": "select avg(is_negative::int) from marts.fct_orders_risk",
    "taxa_atraso": "select avg(is_late::int) from marts.fct_orders_risk",
    "taxa_negativa_atrasados": (
        "select avg(is_negative::int) from marts.fct_orders_risk where is_late"
    ),
    "taxa_negativa_no_prazo": (
        "select avg(is_negative::int) from marts.fct_orders_risk where not is_late"
    ),
    "nota_media_atrasados": "select avg(review_score) from marts.fct_orders_risk where is_late",
    "nota_media_no_prazo": "select avg(review_score) from marts.fct_orders_risk where not is_late",
    "linhas_fct_complaints": "select count(*) from marts.fct_complaints",
    "linhas_fct_orders_causal": "select count(*) from marts.fct_orders_causal",
    "pedidos_sem_distancia": (
        "select count(*) from marts.fct_orders_risk where distance_km is null"
    ),
    "avaliacao_antes_da_entrega": (
        "select count(*) from intermediate.int_order_reviews r "
        "join staging.stg_orders o using (order_id) "
        "where o.delivered_customer_at is not null "
        "and r.review_created_at::date < o.delivered_customer_at::date"
    ),
    "entrega_antes_da_compra": (
        "select count(*) from staging.stg_orders where delivered_customer_at < purchased_at"
    ),
}

DESCRIPTIONS: dict[str, str] = {
    "pedidos": "Pedidos na base",
    "pedidos_entregues": "Pedidos entregues (status delivered, com data de entrega)",
    "compra_min": "Primeira compra",
    "compra_max": "Última compra",
    "avaliacoes": "Avaliações (linhas)",
    "pedidos_com_mais_de_uma_avaliacao": "Pedidos com mais de uma avaliação",
    "avaliacoes_com_comentario": "Avaliações com comentário preenchido",
    "taxa_sem_comentario": "Proporção de avaliações sem comentário",
    "linhas_fct_orders_risk": "Linhas em fct_orders_risk (entregues e avaliados)",
    "taxa_negativa": "Taxa de avaliação negativa (nota 1 ou 2)",
    "taxa_atraso": "Taxa de pedidos atrasados",
    "taxa_negativa_atrasados": "Taxa negativa entre atrasados",
    "taxa_negativa_no_prazo": "Taxa negativa entre entregues no prazo",
    "nota_media_atrasados": "Nota média dos atrasados",
    "nota_media_no_prazo": "Nota média dos entregues no prazo",
    "linhas_fct_complaints": "Reclamações com texto (nota até 3) em fct_complaints",
    "linhas_fct_orders_causal": "Linhas em fct_orders_causal",
    "pedidos_sem_distancia": "Pedidos sem distância (CEP sem coordenada)",
    "avaliacao_antes_da_entrega": "Avaliações criadas antes da entrega (dia)",
    "entrega_antes_da_compra": "Pedidos com entrega antes da compra",
}

SCORE_DISTRIBUTION = """
    select review_score, count(*) as n, count(*) / sum(count(*)) over () as share
    from intermediate.int_order_reviews
    group by review_score
    order by review_score
"""

DELAY_BUCKETS = """
    select
        case
            when delay_days <= -10 then '1. 10+ dias adiantado'
            when delay_days <= 0 then '2. até 10 dias adiantado'
            when delay_days <= 3 then '3. 1 a 3 dias de atraso'
            when delay_days <= 10 then '4. 4 a 10 dias de atraso'
            else '5. mais de 10 dias de atraso'
        end as faixa,
        count(*) as n,
        avg(is_negative::int) as taxa_negativa
    from marts.fct_orders_risk
    group by faixa
    order by faixa
"""


def _fmt(value: object) -> str:
    if isinstance(value, float):
        return f"{value:.4f}" if abs(value) < 10 else f"{value:,.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def collect(con: duckdb.DuckDBPyConnection) -> dict[str, object]:
    """Executa as consultas e devolve os números por nome."""
    return {name: con.execute(sql).fetchone()[0] for name, sql in QUERIES.items()}


def render(con: duckdb.DuckDBPyConnection) -> str:
    """Monta o markdown com todos os números."""
    numbers = collect(con)
    lines = [
        "# Resumo da análise exploratória",
        "",
        "Gerado por `scripts/eda_resumo.py` a partir dos marts do dbt. Não edite à mão.",
        "",
        "| Métrica | Valor |",
        "| --- | ---: |",
    ]
    lines += [f"| {DESCRIPTIONS[k]} | {_fmt(v)} |" for k, v in numbers.items()]

    lines += ["", "## Distribuição das notas (uma avaliação por pedido)", ""]
    lines += ["| Nota | Pedidos | Proporção |", "| ---: | ---: | ---: |"]
    for score, n, share in con.execute(SCORE_DISTRIBUTION).fetchall():
        lines.append(f"| {score} | {_fmt(n)} | {_fmt(share)} |")

    lines += ["", "## Taxa de nota negativa por atraso (fct_orders_risk)", ""]
    lines += ["| Faixa | Pedidos | Taxa negativa |", "| --- | ---: | ---: |"]
    for faixa, n, rate in con.execute(DELAY_BUCKETS).fetchall():
        lines.append(f"| {faixa} | {_fmt(n)} | {_fmt(rate)} |")

    lines += [
        "",
        "A diferença entre atrasados e no prazo é correlação, não efeito causal.",
        "O efeito do atraso é estimado na Fase 3, controlando confundidores.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=Path(os.getenv("DATA_DIR", "data")))
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "eda-resumo.md")
    args = parser.parse_args()

    db_path = args.data_dir / "processed" / "copiloto.duckdb"
    with duckdb.connect(str(db_path), read_only=True) as con:
        text = render(con)
    args.out.write_text(text, encoding="utf-8")
    print(f"Resumo gravado em {args.out}")


if __name__ == "__main__":
    main()
