"""Cliente do LLM por endpoint compatível com OpenAI, com cache em disco.

Mesma entrada (modelo, mensagens, temperatura, formato) devolve a mesma resposta
gravada, sem nova chamada paga. Os testes nunca usam este cliente com rede: usam
o ScriptedLLM (tests/fakes/llm.py) ou respx.
"""

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import openai

from copiloto.core.config import Settings
from copiloto.core.errors import ConfigurationError, ExternalServiceError
from copiloto.core.logging import get_logger

log = get_logger("llm")


@dataclass(frozen=True)
class LLMResponse:
    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    cached: bool = False


class LLMClient(Protocol):
    """Interface usada pelo resto do projeto (real ou falsa)."""

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> LLMResponse: ...


class OpenAICompatibleLLM:
    """Chama `chat.completions` de qualquer provedor compatível (Gemini, Groq)."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        temperature: float = 0.0,
        cache_dir: Path | None = None,
        max_retries: int = 3,
        client: openai.OpenAI | None = None,
    ) -> None:
        self.model = model
        self.temperature = temperature
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self._client = client or openai.OpenAI(base_url=base_url, api_key=api_key, max_retries=0)

    @classmethod
    def from_settings(cls, settings: Settings) -> "OpenAICompatibleLLM":
        missing = [
            name
            for name, value in (
                ("LLM_BASE_URL", settings.llm_base_url),
                ("LLM_API_KEY", settings.llm_api_key),
                ("LLM_MODEL", settings.llm_model),
            )
            if not value
        ]
        if missing:
            raise ConfigurationError(f"Configure no .env: {', '.join(missing)}")
        return cls(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key.get_secret_value(),
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            cache_dir=settings.llm_cache_dir,
        )

    def _cache_path(self, messages: list[dict[str, str]], json_mode: bool) -> Path | None:
        if self.cache_dir is None:
            return None
        key = json.dumps(
            {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "json": json_mode,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.cache_dir / digest[:2] / f"{digest}.json"

    def complete(self, messages: list[dict[str, str]], json_mode: bool = True) -> LLMResponse:
        path = self._cache_path(messages, json_mode)
        if path is not None and path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return LLMResponse(**{**data, "latency_ms": 0, "cached": True})

        kwargs = {"model": self.model, "messages": messages, "temperature": self.temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        for attempt in range(self.max_retries + 1):
            start = time.perf_counter()
            try:
                result = self._client.chat.completions.create(**kwargs)
                break
            except (
                openai.RateLimitError,
                openai.APITimeoutError,
                openai.APIConnectionError,
            ) as exc:
                if attempt == self.max_retries:
                    raise ExternalServiceError(f"LLM indisponível: {type(exc).__name__}") from None
                wait = 2 ** (attempt + 2)
                log.warning("llm_retry", attempt=attempt + 1, wait_s=wait, error=type(exc).__name__)
                time.sleep(wait)
            except openai.APIStatusError as exc:
                raise ExternalServiceError(f"LLM respondeu {exc.status_code}") from None

        usage = result.usage
        response = LLMResponse(
            content=result.choices[0].message.content or "",
            model=result.model or self.model,
            input_tokens=getattr(usage, "prompt_tokens", 0) or 0,
            output_tokens=getattr(usage, "completion_tokens", 0) or 0,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(response), ensure_ascii=False), encoding="utf-8")
        return response
