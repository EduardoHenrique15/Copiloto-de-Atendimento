"""Regrava o snapshot do contrato da API. Rode só quando a mudança de formato for intencional
e o n8n já estiver atualizado: python tests/contract/update_snapshot.py"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from copiloto.api.app import create_app  # noqa: E402
from tests.fakes.api import make_container  # noqa: E402

if __name__ == "__main__":
    container, _ = make_container(with_risk=False)
    schemas = TestClient(create_app(container)).get("/openapi.json").json()["components"]["schemas"]
    out = Path(__file__).with_name("openapi_snapshot.json")
    out.write_text(
        json.dumps(schemas, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"Snapshot gravado em {out}")
