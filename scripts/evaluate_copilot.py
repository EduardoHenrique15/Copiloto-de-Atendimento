"""Avalia o copiloto nos 60 casos fictícios: rascunhos, juiz LLM e concordância com o humano.

Uso (cada etapa pede autorização com --allow-llm; sem ela, só mostra a estimativa):
    python scripts/evaluate_copilot.py --stage drafts --estimate
    python scripts/evaluate_copilot.py --stage drafts --allow-llm
    python scripts/evaluate_copilot.py --stage judge --allow-llm
    python scripts/evaluate_copilot.py            # só refaz o relatório, sem chamar o LLM

Tudo é gravado caso a caso em eval/results/ (retoma se cair). A avaliação humana dos 40
rascunhos é feita em: streamlit run src/copiloto/dashboard/copilot_eval_app.py
"""

import argparse
import json
from pathlib import Path

from copiloto.ai.copilot.policies import load_policies
from copiloto.ai.copilot.prompt import SYSTEM
from copiloto.ai.eval.cases import load_cases
from copiloto.ai.eval.judge import system_prompt as judge_system_prompt
from copiloto.ai.eval.report import render
from copiloto.ai.eval.run import load_human, read_jsonl, run_drafts, run_judge, summarize
from copiloto.core.config import get_settings
from copiloto.core.costs import LLMPrice, llm_cost_brl
from copiloto.core.logging import configure_logging

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "eval" / "copilot_cases.yaml"
RESULTS = ROOT / "eval" / "results"
DRAFTS = RESULTS / "copilot_drafts.jsonl"
JUDGE = RESULTS / "copilot_judge.jsonl"
HUMAN = ROOT / "eval" / "human" / "copilot_human.csv"
CHARS_PER_TOKEN = 3.5
# Saída prevista por chamada (inclui tokens de raciocínio do modelo, como visto na Fase 4).
OUTPUT_TOKENS = {"drafts": 300, "judge": 400}


def estimate(stage: str, remaining: int, k: int, chunks: list) -> tuple[int, int]:
    avg_chunk = sum(len(c.text) for c in chunks) / len(chunks)
    if stage == "drafts":
        chars = len(SYSTEM) + k * (avg_chunk + 80) + 500
    else:
        chars = len(judge_system_prompt()) + k * (avg_chunk + 40) + 1100
    return int(remaining * chars / CHARS_PER_TOKEN), remaining * OUTPUT_TOKENS[stage]


def main() -> None:
    configure_logging("WARNING")
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--stage", choices=["drafts", "judge", "report"], default="report")
    parser.add_argument("--allow-llm", action="store_true", help="autoriza chamadas reais")
    parser.add_argument("--estimate", action="store_true", help="só mostra a estimativa")
    parser.add_argument("--rpm", type=float, default=12)
    args = parser.parse_args()

    cases = load_cases(CASES)
    chunks = load_policies(ROOT / "policies")
    price = LLMPrice.from_settings(settings) if settings.usd_brl else None

    if args.stage != "report":
        drafts = read_jsonl(DRAFTS)
        if args.stage == "drafts":
            remaining = len({c.id for c in cases} - {d["case_id"] for d in drafts})
        else:
            judged = {j["case_id"] for j in read_jsonl(JUDGE)}
            remaining = len({d["case_id"] for d in drafts} - judged)
            if not drafts:
                raise SystemExit("Rode antes a etapa drafts.")
        tokens_in, tokens_out = estimate(args.stage, remaining, settings.rag_top_k, chunks)
        cost = f"R$ {llm_cost_brl(tokens_in, tokens_out, price):.2f}" if price else "n/d"
        print(
            f"{args.stage}: {remaining} chamadas, modelo {settings.llm_model}, "
            f"~{tokens_in:,} tokens de entrada e ~{tokens_out:,} de saída "
            f"(preço pago de referência: {cost}; plano gratuito: R$ 0), "
            f"~{remaining / args.rpm:.0f} min."
        )
        if args.estimate or (remaining and not args.allow_llm):
            print("Nada foi chamado. Use --allow-llm depois da autorização.")
            return
        from copiloto.integrations.llm import OpenAICompatibleLLM

        llm = OpenAICompatibleLLM.from_settings(settings)
        interval = 60 / args.rpm
        if args.stage == "drafts":
            from copiloto.ai.copilot.retrieve import PolicyRetriever
            from copiloto.ai.triage.embeddings_lr import SentenceTransformerEmbedder
            from copiloto.integrations.vectorstore import ChromaVectorStore

            retriever = PolicyRetriever(
                chunks,
                SentenceTransformerEmbedder(settings.embedding_model),
                ChromaVectorStore(settings.chroma_dir),
            )
            if retriever.store.count() == 0:
                retriever.index()
            run_drafts(cases, llm, retriever, settings.rag_top_k, DRAFTS, interval)
        else:
            run_judge(cases, drafts, llm, {c.id: c for c in chunks}, JUDGE, interval)

    drafts = read_jsonl(DRAFTS)
    if not drafts:
        print("Sem rascunhos ainda. Rode a etapa drafts.")
        return
    summary = summarize(cases, drafts, read_jsonl(JUDGE), load_human(HUMAN), price)
    (RESULTS / "copilot_eval.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    md = ROOT / "docs" / "model-cards" / "copiloto-avaliacao.md"
    md.write_text(render(summary), encoding="utf-8")
    checks = summary["checks"]
    print(
        f"{summary['n_cases']} rascunhos | citação {checks['citation']['rate']:.1%} | "
        f"ação {checks['action']['rate']:.1%}"
    )
    if "judge" in summary:
        print(f"Juiz: todos os critérios aprovados em {summary['judge']['all_pass_rate']:.1%}")
    if "agreement" in summary:
        a = summary["agreement"]
        print(
            f"Concordância com o humano ({a['n_cases']} casos): {a['overall_agreement']:.1%}, "
            f"kappa {a['overall_kappa']}; aceitável: {a['acceptable']}"
        )
    print(f"Relatório: {md}")


if __name__ == "__main__":
    main()
