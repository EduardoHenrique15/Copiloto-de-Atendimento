"""Rotulagem fraca com o LLM (conjunto prata).

Exclui as reclamações do conjunto ouro e da leitura da taxonomia, para que a
avaliação nunca use textos vistos pelo LLM nesta etapa.

Uso:
    python scripts/weak_label.py --estimate             # só estimativa, sem chamar o LLM
    python scripts/weak_label.py --run --max-calls 1    # piloto: 1 chamada
    python scripts/weak_label.py --run                  # tudo (retoma de onde parou)

Saídas: data/labels/silver.csv (só ids e rótulos) e eval/results/weak_label_run.json.
"""

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from copiloto.ai.labeling.sampling import load_complaints, stratified_sample
from copiloto.ai.labeling.weak import PROMPT_VERSION, estimate, run_weak_labeling
from copiloto.core.config import get_settings
from copiloto.core.costs import LLMPrice, llm_cost_brl
from copiloto.core.logging import configure_logging
from copiloto.integrations.llm import OpenAICompatibleLLM

ROOT = Path(__file__).resolve().parents[1]
SILVER = ROOT / "data" / "labels" / "silver.csv"
SEED_SILVER = 99


def silver_pool(settings, n: int) -> pd.DataFrame:
    complaints = load_complaints(settings.duckdb_path)
    gold = set(pd.read_csv(ROOT / "data" / "labels" / "gold_sample.csv")["complaint_id"])
    taxonomy = set(
        pd.read_csv(settings.processed_dir / "taxonomia" / "amostra.csv")["complaint_id"]
    )
    sample = stratified_sample(complaints, n, seed=SEED_SILVER, exclude=gold | taxonomy)
    title = sample["comment_title"].fillna("")
    sample["text"] = (
        title.where(title == "", "[" + title + "] ") + sample["comment_message"]
    ).str.strip()
    return sample[["complaint_id", "text"]]


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--estimate", action="store_true")
    mode.add_argument("--run", action="store_true")
    parser.add_argument("--n", type=int, default=4000, help="tamanho do conjunto prata")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--max-calls", type=int, default=450, help="limite de chamadas novas")
    parser.add_argument("--rpm", type=float, default=12, help="chamadas por minuto (limite 15)")
    args = parser.parse_args()

    pool = silver_pool(settings, args.n)
    done = set(pd.read_csv(SILVER)["complaint_id"]) if SILVER.exists() else set()
    todo = pool[~pool["complaint_id"].isin(done)]
    est = estimate(todo["text"].tolist(), args.batch_size)

    cost = "preço não configurado (LLM_PRICE_* e USD_BRL no .env)"
    if settings.usd_brl:
        price = LLMPrice.from_settings(settings)
        cost = f"R$ {llm_cost_brl(est.input_tokens, est.output_tokens, price):.2f}"
    print(
        f"Conjunto prata: {len(pool)} reclamações, {len(done)} já rotuladas, faltam {len(todo)}.\n"
        f"Estimativa: {est.calls} chamadas de {args.batch_size} comentários, "
        f"~{est.input_tokens:,} tokens de entrada e ~{est.output_tokens:,} de saída. "
        f"Custo estimado: {cost}.\n"
        f"Modelo: {settings.llm_model} | prompt {PROMPT_VERSION} | "
        f"ritmo {args.rpm:g} chamadas/min (~{est.calls / args.rpm:.0f} min)."
    )
    if args.estimate:
        return

    llm = OpenAICompatibleLLM.from_settings(settings)

    def save(batch: pd.DataFrame, _: dict) -> None:
        SILVER.parent.mkdir(parents=True, exist_ok=True)
        batch.to_csv(SILVER, mode="a", header=not SILVER.exists(), index=False)

    stats = run_weak_labeling(
        llm, todo, args.batch_size, args.max_calls, save, min_interval_s=60 / args.rpm
    )
    silver = pd.read_csv(SILVER)
    report = {
        "finished_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "model": settings.llm_model,
        "prompt_version": PROMPT_VERSION,
        "batch_size": args.batch_size,
        "this_run": stats,
        "total_labeled": len(silver),
        "label_distribution": silver["label"].value_counts().to_dict(),
        "multiple_problems_rate": float(silver["multiple_problems"].mean()),
    }
    out = ROOT / "eval" / "results" / "weak_label_run.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
