"""Demonstração ponta a ponta da API com o LLM real: triagem, rascunho e decisão.

Usa uma reclamação real da base (escolhida pela semente) e um banco SQLite local
(data/processed/demo.db). Chamadas ao LLM: 1 no rascunho (+1 na triagem se
TRIAGE_BACKEND=zero_shot). Só rode com autorização.

Uso: python scripts/demo_api.py --allow-llm [--seed 1]
"""

import argparse
import json

from fastapi.testclient import TestClient

from copiloto.ai.labeling.sampling import load_complaints
from copiloto.ai.triage.data import complaint_texts
from copiloto.api.app import create_app
from copiloto.api.container import build_container
from copiloto.core.config import get_settings
from copiloto.core.logging import configure_logging


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--allow-llm", action="store_true")
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    if not args.allow_llm:
        raise SystemExit("Esta demonstração chama o LLM real. Use --allow-llm com autorização.")

    settings = get_settings()
    configure_logging("WARNING")
    settings = settings.model_copy(
        update={"database_url": f"sqlite:///{settings.processed_dir / 'demo.db'}"}
    )
    client = TestClient(create_app(build_container(settings)))
    headers = {"X-API-Key": settings.api_key.get_secret_value()}

    complaints = load_complaints(settings.duckdb_path)
    row = complaints.sample(1, random_state=args.seed).iloc[0]
    ticket = f"demo-{row['complaint_id'][:12]}"
    text = complaint_texts(complaints.loc[[row.name]]).iloc[0]
    print(f"Reclamação: {text}\n")

    for name, method, path, body in (
        (
            "triagem",
            "post",
            "/triage",
            {"ticket_id": ticket, "text": text, "order_id": row["order_id"]},
        ),
        ("rascunho", "post", "/draft", {"ticket_id": ticket}),
    ):
        r = getattr(client, method)(path, json=body, headers=headers)
        print(
            f"--- {name} ({r.status_code})\n{json.dumps(r.json(), indent=2, ensure_ascii=False)}\n"
        )
    print(json.dumps(client.get("/metrics?period=day", headers=headers).json(), indent=2))


if __name__ == "__main__":
    main()
