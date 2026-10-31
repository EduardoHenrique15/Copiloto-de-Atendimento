"""Cliente do LLM com HTTP simulado (respx): formato da chamada, cache e erros."""

import json

import httpx
import openai
import pytest
import respx

from copiloto.core.config import Settings
from copiloto.core.errors import ConfigurationError, ExternalServiceError
from copiloto.integrations.llm import OpenAICompatibleLLM

BASE = "https://llm.exemplo.test/v1/"
MESSAGES = [{"role": "user", "content": "oi"}]


def _ok(content='{"status": "ok"}'):
    return httpx.Response(
        200,
        json={
            "id": "x",
            "object": "chat.completion",
            "created": 0,
            "model": "modelo-teste",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": content},
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        },
    )


def _llm(tmp_path, retries=0):
    # trust_env=False: ignora proxies do ambiente, para o respx interceptar a chamada.
    client = openai.OpenAI(
        base_url=BASE,
        api_key="chave-falsa",
        max_retries=0,
        http_client=httpx.Client(trust_env=False),
    )
    return OpenAICompatibleLLM(
        BASE, "chave-falsa", "modelo-teste", cache_dir=tmp_path, max_retries=retries, client=client
    )


@respx.mock
def test_sends_json_mode_and_reads_usage(tmp_path):
    route = respx.post(f"{BASE}chat/completions").mock(return_value=_ok())
    r = _llm(tmp_path).complete(MESSAGES)
    sent = route.calls.last.request
    body = json.loads(sent.read())
    assert body["response_format"] == {"type": "json_object"}
    assert body["temperature"] == 0.0
    assert sent.headers["authorization"] == "Bearer chave-falsa"
    assert (r.content, r.input_tokens, r.output_tokens, r.cached) == (
        '{"status": "ok"}',
        10,
        5,
        False,
    )


@respx.mock
def test_same_input_is_served_from_disk_cache(tmp_path):
    route = respx.post(f"{BASE}chat/completions").mock(return_value=_ok())
    llm = _llm(tmp_path)
    first = llm.complete(MESSAGES)
    second = llm.complete(MESSAGES)
    assert route.call_count == 1
    assert second.cached and second.content == first.content
    llm.complete([{"role": "user", "content": "outra"}])
    assert route.call_count == 2


@respx.mock
def test_rate_limit_is_retried(tmp_path, monkeypatch):
    monkeypatch.setattr("copiloto.integrations.llm.time.sleep", lambda s: None)
    route = respx.post(f"{BASE}chat/completions").mock(
        side_effect=[httpx.Response(429, json={"error": {"message": "limite"}}), _ok()]
    )
    assert _llm(tmp_path, retries=2).complete(MESSAGES).content == '{"status": "ok"}'
    assert route.call_count == 2


@respx.mock
def test_overloaded_server_is_retried(tmp_path, monkeypatch):
    waits = []
    monkeypatch.setattr("copiloto.integrations.llm.time.sleep", waits.append)
    route = respx.post(f"{BASE}chat/completions").mock(
        side_effect=[
            httpx.Response(503, json={"error": {"message": "sobrecarregado"}}),
            httpx.Response(503, json={"error": {"message": "sobrecarregado"}}),
            _ok(),
        ]
    )
    assert _llm(tmp_path, retries=3).complete(MESSAGES).content == '{"status": "ok"}'
    assert route.call_count == 3
    assert waits == [4, 8]


@respx.mock
def test_gives_up_after_max_retries(tmp_path, monkeypatch):
    monkeypatch.setattr("copiloto.integrations.llm.time.sleep", lambda s: None)
    respx.post(f"{BASE}chat/completions").mock(
        return_value=httpx.Response(503, json={"error": {"message": "fora do ar"}})
    )
    with pytest.raises(ExternalServiceError, match="indisponível"):
        _llm(tmp_path, retries=2).complete(MESSAGES)


@respx.mock
def test_errors_do_not_leak_details(tmp_path):
    respx.post(f"{BASE}chat/completions").mock(
        return_value=httpx.Response(401, json={"error": {"message": "chave inválida"}})
    )
    with pytest.raises(ExternalServiceError, match="401"):
        _llm(tmp_path).complete(MESSAGES)


def test_from_settings_requires_configuration(monkeypatch):
    for var in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ConfigurationError, match="LLM_API_KEY"):
        OpenAICompatibleLLM.from_settings(Settings(_env_file=None))
