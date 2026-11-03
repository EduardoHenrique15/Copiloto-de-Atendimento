"""Roda a avaliação do copiloto: rascunhos, juiz e resumo. Grava tudo de forma incremental."""

import json
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from copiloto.ai.copilot.draft import FALLBACK_RESPONSE, generate_draft
from copiloto.ai.copilot.policies import PolicyChunk
from copiloto.ai.copilot.prompt import PROMPT_VERSION
from copiloto.ai.eval.agreement import judge_agreement
from copiloto.ai.eval.cases import CopilotCase
from copiloto.ai.eval.checks import check_draft, summarize_checks
from copiloto.ai.eval.judge import CRITERIA, JUDGE_VERSION, judge_draft
from copiloto.ai.guardrails.pii import mask_pii
from copiloto.core.costs import LLMPrice, cost_per_thousand_brl
from copiloto.integrations.llm import LLMClient

HUMAN_COLUMNS = ["case_id", *CRITERIA, "nota", "evaluated_at"]
# A avaliação humana (eval/human/copilot_human.csv) foi feita sobre os rascunhos desta versão.
HUMAN_DRAFT_VERSION = "draft-v1"


def result_paths(results_dir: Path, version: str) -> dict[str, Path]:
    """Arquivos de uma versão do copiloto: cada versão tem os seus, para comparar antes e depois."""
    return {
        "drafts": results_dir / f"copilot_drafts_{version}.jsonl",
        "judge": results_dir / f"copilot_judge_{version}.jsonl",
        "summary": results_dir / f"copilot_eval_{version}.json",
    }


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _append(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_drafts(
    cases: list[CopilotCase],
    llm: LLMClient,
    retriever,  # noqa: ANN001 - PolicyRetriever ou um dublê com o mesmo retrieve()
    k: int,
    out_path: Path,
    min_interval_s: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict]:
    """Um rascunho por caso. Casos já gravados em `out_path` não são refeitos."""
    done = {r["case_id"] for r in read_jsonl(out_path)}
    for case in cases:
        if case.id in done:
            continue
        result = generate_draft(llm, retriever, case.complaint, case.category, case.order, k)
        record = asdict(result)
        record.pop("events")
        record["case_id"] = case.id
        _append(out_path, record)
        if min_interval_s:
            sleep(min_interval_s)
    return read_jsonl(out_path)


def run_judge(
    cases: list[CopilotCase],
    drafts: list[dict],
    llm: LLMClient,
    chunks: dict[str, PolicyChunk],
    out_path: Path,
    min_interval_s: float = 0.0,
    sleep: Callable[[float], None] = time.sleep,
) -> list[dict]:
    """Um julgamento por rascunho. O juiz vê as mesmas políticas que o redator recebeu."""
    by_id = {c.id: c for c in cases}
    done = {r["case_id"] for r in read_jsonl(out_path)}
    for draft in drafts:
        if draft["case_id"] in done:
            continue
        case = by_id[draft["case_id"]]
        complaint, _ = mask_pii(case.complaint)
        policies = [chunks[i] for i in draft["retrieved"] if i in chunks]
        output, response = judge_draft(llm, complaint, case.order, policies, draft)
        _append(
            out_path,
            {
                "case_id": case.id,
                "judge_prompt": JUDGE_VERSION,
                "verdicts": output.model_dump() if output else None,
                "input_tokens": response.input_tokens,
                "output_tokens": response.output_tokens,
            },
        )
        if min_interval_s:
            sleep(min_interval_s)
    return read_jsonl(out_path)


def load_human(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path, dtype={"case_id": str})
    return {row["case_id"]: {c: bool(row[c]) for c in CRITERIA} for row in frame.to_dict("records")}


def summarize(
    cases: list[CopilotCase],
    drafts: list[dict],
    judges: list[dict],
    human: dict[str, dict],
    price: LLMPrice | None = None,
) -> dict:
    by_id = {c.id: c for c in cases}
    drafts = [d for d in drafts if d["case_id"] in by_id]
    checks = [check_draft(by_id[d["case_id"]], d) for d in drafts]
    flags = Counter(f for d in drafts for f in d["guardrail_flags"])
    lat = np.asarray([d["latency_ms"] for d in drafts], dtype=float)
    cost: dict = {
        "draft_p50_ms": float(np.percentile(lat, 50)),
        "draft_p95_ms": float(np.percentile(lat, 95)),
    }
    if price:
        cost["draft_per_1000_brl"] = cost_per_thousand_brl(
            float(np.mean([d["input_tokens"] for d in drafts])),
            float(np.mean([d["output_tokens"] for d in drafts])),
            price,
        )
    summary = {
        "n_cases": len(drafts),
        "draft_prompt": drafts[0]["prompt_version"] if drafts else PROMPT_VERSION,
        "model": drafts[0]["model"] if drafts else "",
        "checks": summarize_checks(checks),
        "per_case_checks": {d["case_id"]: c for d, c in zip(drafts, checks, strict=True)},
        "guardrails": {
            "any_rate": sum(bool(d["guardrail_flags"]) for d in drafts) / len(drafts),
            "fallback_rate": sum(d["response"] == FALLBACK_RESPONSE for d in drafts) / len(drafts),
            "by_flag": dict(sorted(flags.items())),
        },
        "cost": cost,
    }
    valid = [j for j in judges if j["case_id"] in by_id]
    ok = [j for j in valid if j["verdicts"]]
    if valid:
        summary["judge_prompt"] = valid[0]["judge_prompt"]
        summary["judge"] = {
            "n": len(valid),
            "failures": len(valid) - len(ok),
            "pass_rate": {
                c: sum(j["verdicts"][c]["ok"] for j in ok) / len(ok) if ok else None
                for c in CRITERIA
            },
            "all_pass_rate": sum(all(j["verdicts"][c]["ok"] for c in CRITERIA) for j in ok)
            / len(ok)
            if ok
            else None,
        }
        if price:
            cost["judge_per_1000_brl"] = cost_per_thousand_brl(
                float(np.mean([j["input_tokens"] for j in valid])),
                float(np.mean([j["output_tokens"] for j in valid])),
                price,
            )
    judge_bools = {j["case_id"]: {c: j["verdicts"][c]["ok"] for c in CRITERIA} for j in ok}
    if human and judge_bools:
        summary["agreement"] = judge_agreement(human, judge_bools)
    return summary
