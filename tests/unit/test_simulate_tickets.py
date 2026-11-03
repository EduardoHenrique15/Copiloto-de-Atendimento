import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from simulate_tickets import payload, pick  # noqa: E402


def test_pick_skips_gold_and_is_reproducible():
    df = pd.DataFrame(
        {
            "complaint_id": [f"{i:032d}" for i in range(10)],
            "order_id": [f"o{i}" for i in range(10)],
            "text": ["t"] * 10,
        }
    )
    gold = {f"{i:032d}" for i in range(5)}
    a = pick(df, 3, 7, gold)
    assert set(a["complaint_id"]).isdisjoint(gold)
    assert a.equals(pick(df, 3, 7, gold))
    body = payload(a.iloc[0])
    assert set(body) == {"ticket_id", "text", "order_id"} and body["ticket_id"].startswith("sim-")
