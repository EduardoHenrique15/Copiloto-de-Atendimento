"""Simula a chegada de reclamações: envia comentários reais da base ao webhook do n8n.

Uso:
    python scripts/simulate_tickets.py --n 3 --dry-run       # só mostra o que enviaria
    python scripts/simulate_tickets.py --n 3 --interval 20   # envia 3, uma a cada 20 s

Cada reclamação enviada gera chamadas reais ao LLM na API: 1 na triagem (zero-shot) e
mais 1 no rascunho, se o fluxo de aprovação for acionado. Rode só com autorização.
O texto vai para a API, que mascara dados pessoais antes do LLM e antes de gravar.
"""

import argparse
import json
import random
import time
import urllib.request
from pathlib import Path

import pandas as pd

from copiloto.ai.labeling.sampling import load_complaints
from copiloto.ai.triage.data import complaint_texts
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_URL = "http://localhost:5678/webhook/triagem"


def pick(complaints: pd.DataFrame, n: int, seed: int, exclude: set[str]) -> pd.DataFrame:
    """Sorteio fixo, sem os itens do conjunto ouro (eles são da avaliação)."""
    pool = complaints[~complaints["complaint_id"].isin(exclude)]
    return pool.sample(n=n, random_state=seed)


def payload(row: pd.Series) -> dict:
    return {
        "ticket_id": f"sim-{row['complaint_id'][:12]}",
        "text": row["text"],
        "order_id": row["order_id"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=3)
    parser.add_argument("--interval", type=float, default=20, help="segundos entre envios")
    parser.add_argument("--seed", type=int, default=None, help="padrão: sorteio novo a cada vez")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    complaints = load_complaints(get_settings().duckdb_path)
    complaints["text"] = complaint_texts(complaints)
    gold = pd.read_csv(ROOT / "data" / "labels" / "gold_sample.csv", dtype=str)
    seed = args.seed if args.seed is not None else random.randrange(1_000_000)
    chosen = pick(complaints, args.n, seed, set(gold["complaint_id"]))
    print(f"{len(chosen)} reclamações (semente {seed}) para {args.url}")
    for i, (_, row) in enumerate(chosen.iterrows(), start=1):
        body = payload(row)
        print(f"{i}. {body['ticket_id']}: {body['text'][:70]}...")
        if args.dry_run:
            continue
        request = urllib.request.Request(
            args.url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            print(f"   enviado (HTTP {response.status})")
        if i < len(chosen):
            time.sleep(args.interval)
    if args.dry_run:
        print("Nada foi enviado (--dry-run).")


if __name__ == "__main__":
    main()
