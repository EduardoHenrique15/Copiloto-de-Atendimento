"""Pedidos sintéticos com o mesmo formato de marts.fct_orders_risk.

O alvo depende de atraso e da nota anterior do vendedor, com ruído, para que
um modelo bom tenha algo a aprender e o baseline seja superável.
"""

import numpy as np
import pandas as pd


def make_risk_frame(n: int = 4000, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    purchased = pd.Timestamp("2017-01-01") + pd.to_timedelta(
        np.sort(rng.uniform(0, 540, n)), unit="D"
    )
    promised = rng.uniform(10, 40, n)
    delay = rng.normal(-10, 8, n)
    delivered = purchased + pd.to_timedelta(promised + delay, unit="D")
    delivered = delivered.where(delivered > purchased, purchased + pd.Timedelta(days=1))
    review_created = delivered + pd.to_timedelta(rng.uniform(0, 5, n), unit="D")
    seller_avg = np.clip(rng.normal(4.1, 0.5, n), 1, 5)
    seller_avg[rng.random(n) < 0.1] = np.nan
    is_late = delay > 0
    logit = (
        -2.6
        + 2.4 * is_late
        + 0.06 * np.clip(delay, 0, None)
        - 0.9 * np.nan_to_num(seller_avg - 4.1)
    )
    y = rng.random(n) < 1 / (1 + np.exp(-logit))
    categories = np.array(["bed_bath_table", "health_beauty", "sports", "toys"])
    states = np.array(["SP", "RJ", "MG", "BA"])
    return pd.DataFrame(
        {
            "order_id": [f"o{i}" for i in range(n)],
            "seller_id": rng.choice([f"s{i}" for i in range(50)], n),
            "purchased_at": purchased,
            "feature_cutoff_at": delivered,
            "estimated_delivery_at": purchased + pd.to_timedelta(promised, unit="D"),
            "promised_days": promised,
            "delivery_days": (delivered - purchased).total_seconds() / 86400,
            "delay_days": delay,
            "is_late": is_late,
            "n_items": rng.integers(1, 4, n),
            "n_products": rng.integers(1, 3, n),
            "n_sellers": rng.integers(1, 2, n),
            "items_price": rng.gamma(2, 60, n),
            "freight_value": rng.gamma(2, 10, n),
            "freight_ratio": rng.uniform(0.05, 0.6, n),
            "main_category": rng.choice(categories, n),
            "main_payment_type": rng.choice(["credit_card", "boleto"], n),
            "max_installments": rng.integers(1, 10, n),
            "n_payment_types": rng.integers(1, 3, n),
            "customer_state": rng.choice(states, n),
            "seller_state": rng.choice(states, n),
            "same_state": rng.random(n) < 0.4,
            "distance_km": rng.uniform(1, 2500, n),
            "seller_prior_orders": rng.integers(0, 300, n),
            "seller_prior_avg_score": seller_avg,
            "seller_prior_n_reviews": rng.integers(0, 300, n),
            "seller_prior_late_rate": rng.uniform(0, 0.3, n),
            "seller_prior_n_delivered": rng.integers(0, 300, n),
            "review_created_at": review_created,
            "review_score": np.where(y, rng.integers(1, 3, n), rng.integers(3, 6, n)),
            "is_negative": y,
        }
    )
