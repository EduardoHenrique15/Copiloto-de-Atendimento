"""Avalia as abordagens de triagem no conjunto ouro humano.

Uso:
    python scripts/evaluate_triage.py --split val --approaches embeddings_lr
    python scripts/evaluate_triage.py --split val --approaches zero_shot --estimate
    python scripts/evaluate_triage.py --split val --approaches zero_shot --allow-llm
    python scripts/evaluate_triage.py --split test --approaches embeddings_lr,zero_shot \
        --final --allow-llm

A divisão `test` só roda com --final: ela é usada uma única vez, na comparação final.
As previsões ficam em eval/results/triage_preds_<split>_<abordagem>.csv (retoma se cair).
Uma abordagem só entra na tabela se tiver previsões para todos os itens.
Previsões do BERTimbau (Colab) entram se o arquivo triage_preds_<split>_bertimbau.csv existir.
"""

import argparse
import json
from pathlib import Path

import pandas as pd

from copiloto.ai.triage import zero_shot
from copiloto.ai.triage.compare import predict_split, render, summarize
from copiloto.ai.triage.data import load_gold
from copiloto.ai.triage.embeddings_lr import EmbeddingsLRTriager
from copiloto.core.config import get_settings
from copiloto.core.costs import LLMPrice
from copiloto.core.logging import configure_logging
from copiloto.integrations.llm import OpenAICompatibleLLM

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "eval" / "results"
# Premissa: preço-hora de uma máquina de 2 vCPUs em nuvem, em reais (ADR 0009).
CPU_BRL_PER_HOUR = 0.50


def main() -> None:
    settings = get_settings()
    configure_logging("WARNING")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--split", choices=["val", "test"], required=True)
    parser.add_argument("--approaches", default="embeddings_lr")
    parser.add_argument("--allow-llm", action="store_true", help="autoriza chamadas reais")
    parser.add_argument("--estimate", action="store_true", help="só mostra a estimativa")
    parser.add_argument("--final", action="store_true", help="obrigatório para o teste")
    parser.add_argument("--rpm", type=float, default=12)
    parser.add_argument("--target-accuracy", type=float, default=0.85)
    args = parser.parse_args()

    if args.split == "test" and not args.final:
        raise SystemExit("O teste é usado uma única vez, na comparação final. Use --final.")
    gold = load_gold(ROOT / "data" / "labels", settings.duckdb_path, args.split)
    price = LLMPrice.from_settings(settings) if settings.usd_brl else None
    approaches = [a.strip() for a in args.approaches.split(",") if a.strip()]

    results = {}
    for name in approaches:
        cache = RESULTS / f"triage_preds_{args.split}_{name}.csv"
        if name == "embeddings_lr":
            triager = EmbeddingsLRTriager.load(ROOT / "models" / "triage" / "embeddings_lr.joblib")
            frame = predict_split(triager, gold, cache)
        elif name == "zero_shot":
            done = len(pd.read_csv(cache)) if cache.exists() else 0
            remaining = len(gold) - done
            print(
                f"zero_shot: {remaining} chamadas (1 por ticket), modelo {settings.llm_model}, "
                f"prompt {zero_shot.PROMPT_VERSION}, ~{remaining / args.rpm:.0f} min."
            )
            if args.estimate or (remaining and not args.allow_llm):
                print("Nada foi chamado. Use --allow-llm depois da autorização.")
                continue
            triager = zero_shot.ZeroShotTriager(OpenAICompatibleLLM.from_settings(settings))
            frame = predict_split(triager, gold, cache, min_interval_s=60 / args.rpm)
        elif name == "bertimbau":
            if not cache.exists():
                print("bertimbau: sem previsões (rode o notebook no Colab).")
                continue
            frame = gold.merge(pd.read_csv(cache), on="complaint_id", how="inner")
        else:
            raise SystemExit(f"Abordagem desconhecida: {name}")
        if len(frame) < len(gold):
            print(f"{name}: só {len(frame)} de {len(gold)} previsões; fora da tabela.")
            continue
        results[name] = summarize(
            frame, price, CPU_BRL_PER_HOUR, target_accuracy=args.target_accuracy
        )

    if not results:
        return
    out = RESULTS / f"triage_comparison_{args.split}.json"
    previous = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {}
    merged = {**previous, **results}
    out.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_name = "triagem-resultados.md" if args.split == "test" else "triagem-validacao.md"
    md = ROOT / "docs" / "model-cards" / md_name
    md.write_text(render(args.split, merged), encoding="utf-8")
    for name, r in merged.items():
        q = r["quality"]
        print(f"{name}: F1 macro {q['macro_f1']:.3f} | acurácia {q['accuracy']:.1%}")
    print(f"Relatório: {md}")


if __name__ == "__main__":
    main()
