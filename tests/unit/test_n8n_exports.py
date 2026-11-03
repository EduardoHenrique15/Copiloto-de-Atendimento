"""Os fluxos exportados do n8n (n8n/workflows/*.json) não podem levar segredos para o git.

Seção 10.3: nenhum token, senha ou URL com credencial. As credenciais são só referências
por nome (criadas pelo Eduardo dentro do n8n), e os valores de configuração vêm de $env.
"""

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FILES = sorted((ROOT / "n8n" / "workflows").glob("*.json"))
CREDENTIAL_NAMES = {"Copiloto API", "Trello Copiloto", "Telegram Copiloto", "E-mail de teste"}
SECRET_PATTERNS = [
    re.compile(r"\d{8,10}:[A-Za-z0-9_-]{30,}"),  # token de bot do Telegram
    re.compile(r"\b[a-f0-9]{32}\b"),  # API key do Trello
    re.compile(r"\b[a-f0-9]{64}\b"),  # token do Trello
    re.compile(r"AIza[0-9A-Za-z_-]{30,}"),  # chave do Google
    re.compile(r"gsk_[0-9A-Za-z]{20,}"),  # chave do Groq
    re.compile(r"https?://[^/\s\"]+:[^@\s\"]+@"),  # URL com usuário e senha
    re.compile(r"(?i)\"(password|senha|apikey|api_key|token|accesstoken)\"\s*:\s*\"[^\"]+\""),
    re.compile(r"(?i)x-api-key\"?\s*[:=]"),
    re.compile(r"[\w.+-]+@(?!example\.com)[\w-]+\.[\w.]+"),  # e-mail real escrito no fluxo
]


def test_four_flows_exist():
    assert [f.name for f in FILES] == [
        "01-triagem.json",
        "02-aprovacao.json",
        "03-proativo.json",
        "04-monitoramento.json",
    ]


@pytest.mark.parametrize("path", FILES, ids=[f.name for f in FILES])
def test_no_secrets(path):
    text = path.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        assert not pattern.search(text), f"{path.name}: padrão suspeito {pattern.pattern}"


@pytest.mark.parametrize("path", FILES, ids=[f.name for f in FILES])
def test_credentials_are_references_only(path):
    workflow = json.loads(path.read_text(encoding="utf-8"))
    for node in workflow["nodes"]:
        for ref in node.get("credentials", {}).values():
            assert set(ref) == {"id", "name"}, node["name"]
            assert ref["name"] in CREDENTIAL_NAMES, node["name"]
    assert "pinData" not in workflow or workflow["pinData"] == {}  # sem dados de execução


@pytest.mark.parametrize("path", FILES, ids=[f.name for f in FILES])
def test_config_comes_from_env(path):
    text = path.read_text(encoding="utf-8")
    assert "TELEGRAM_CHAT_ID }}" in text or "telegram" not in text.lower()
    if "toEmail" in text:
        assert '"toEmail": "={{ $env.TEST_EMAIL_TO }}"' in text  # e-mail só para o de teste
    assert "localhost:8000" not in text  # a API vem de COPILOTO_API_URL
