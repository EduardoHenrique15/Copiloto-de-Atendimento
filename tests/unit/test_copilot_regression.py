"""Casos de regressão do copiloto (eval/regression_cases.yaml), com o LLM falso.

Rodam no CI: se um guardrail, o roteamento para humano ou o formato de saída mudar sem
querer, algum caso quebra.
"""

from pathlib import Path

import pytest
import yaml

from copiloto.ai.copilot.draft import FALLBACK_RESPONSE, generate_draft
from copiloto.ai.copilot.policies import load_policies
from tests.fakes.llm import ScriptedLLM

ROOT = Path(__file__).resolve().parents[2]
CASES = yaml.safe_load((ROOT / "eval" / "regression_cases.yaml").read_text(encoding="utf-8"))
CHUNKS = {c.id: c for c in load_policies(ROOT / "policies")}


class FixedRetriever:
    """Devolve sempre os trechos listados no caso, para o teste não depender da busca."""

    def __init__(self, ids: list[str]) -> None:
        self.chunks = [CHUNKS[i] for i in ids]

    def retrieve(self, complaint, category, k):  # noqa: ANN001, ANN201
        return self.chunks[:k]


def test_regression_cases_are_well_formed():
    assert len(CASES) >= 8
    assert len({c["id"] for c in CASES}) == len(CASES)
    for case in CASES:
        assert set(case["retrieved"]) <= set(CHUNKS)


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_regression_case(case):
    output = case["llm_output"]
    llm = ScriptedLLM(responses=[output, output])  # a segunda cobre a nova tentativa
    result = generate_draft(
        llm,
        FixedRetriever(case["retrieved"]),
        case["complaint"],
        case["category"],
        case["order"],
        k=4,
    )
    expected = case["expected"]
    assert result.suggested_action == expected["action"]
    assert result.needs_human is expected["needs_human"]
    assert result.guardrail_flags == sorted(expected["flags"])
    assert (result.response == FALLBACK_RESPONSE) is expected["fallback"]
    assert result.policies_cited == expected["cited"]
    assert "123.456.789-09" not in result.response
    # o texto mascarado é o que vai ao LLM
    assert "123.456.789-09" not in llm.calls[0][1]["content"]
