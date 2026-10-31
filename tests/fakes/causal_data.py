"""Pedidos sintéticos com efeito causal conhecido do atraso.

A distância e a nota anterior do vendedor aumentam ao mesmo tempo a chance de
atraso e a chance de nota negativa (confundimento). O atraso soma exatamente
`TRUE_EFFECT` à probabilidade de nota negativa de cada pedido, então o ATT e o
ATE verdadeiros são iguais a `TRUE_EFFECT`.
"""

import numpy as np
import pandas as pd

TRUE_EFFECT = 0.25


def make_causal_frame(n: int = 20000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    distance = rng.uniform(0, 3000, n)
    seller_avg = np.clip(rng.normal(4.1, 0.5, n), 1, 5)
    state = rng.choice(["SP", "RJ", "MG", "BA"], n, p=[0.5, 0.2, 0.2, 0.1])
    logit_t = -3.0 + 0.0009 * distance - 0.8 * (seller_avg - 4.1) + 0.5 * (state == "BA")
    t = rng.random(n) < 1 / (1 + np.exp(-logit_t))
    base = np.clip(0.05 + 0.00003 * distance - 0.06 * (seller_avg - 4.1), 0.01, 0.6)
    y = rng.random(n) < base + TRUE_EFFECT * t
    score = np.where(y, rng.integers(1, 3, n), rng.integers(3, 6, n))
    month = pd.Timestamp("2017-01-01") + pd.to_timedelta(rng.integers(0, 18, n) * 30, unit="D")
    return pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(n)],
            "purchase_month": month.to_period("M").to_timestamp(),
            "is_late": t,
            "is_negative": y,
            "review_score": score,
            "promised_days": rng.uniform(10, 40, n),
            "distance_km": distance,
            "same_state": rng.random(n) < 0.4,
            "customer_state": state,
            "seller_state": rng.choice(["SP", "PR"], n),
            "main_category": rng.choice(["a", "b", "c"], n),
            "n_items": rng.integers(1, 3, n),
            "n_sellers": np.ones(n, int),
            "items_price": rng.gamma(2, 60, n),
            "freight_value": rng.gamma(2, 10, n),
            "freight_ratio": rng.uniform(0.05, 0.6, n),
            "main_payment_type": rng.choice(["credit_card", "boleto"], n),
            "max_installments": rng.integers(1, 10, n),
            "seller_prior_orders": rng.integers(0, 300, n),
            "seller_prior_avg_score": seller_avg,
            "seller_prior_late_rate": rng.uniform(0, 0.3, n),
        }
    )
