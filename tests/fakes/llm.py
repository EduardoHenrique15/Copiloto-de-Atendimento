"""LLM falso para testes: devolve respostas roteirizadas e registra as chamadas."""

import json
from collections.abc import Callable

from copiloto.integrations.llm import LLMResponse


class ScriptedLLM:
    """Cada chamada devolve a próxima resposta da lista, ou o resultado de `responder`."""

    def __init__(
        self,
        responses: list[str | dict] | None = None,
        responder: Callable[[list[dict[str, str]]], str | dict] | None = None,
    ) -> None:
        self.responses = list(responses or [])
        self.responder = responder
        self.calls: list[list[dict[str, str]]] = []

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> LLMResponse:
        self.calls.append(messages)
        if self.responder is not None:
            content = self.responder(messages)
        elif self.responses:
            content = self.responses.pop(0)
        else:
            raise AssertionError("ScriptedLLM sem respostas restantes.")
        if isinstance(content, dict):
            content = json.dumps(content, ensure_ascii=False)
        return LLMResponse(
            content=content,
            model="scripted",
            input_tokens=sum(len(m["content"]) for m in messages) // 4,
            output_tokens=len(content) // 4,
            latency_ms=1,
        )
