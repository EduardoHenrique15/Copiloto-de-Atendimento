"""Sorteio determinístico de grupo por pedido."""

import hashlib

BUCKETS = 10_000


def assign_group(order_id: str, seed: int, treatment_share: float = 0.5) -> str:
    """Devolve "treatment" ou "control".

    O grupo depende só do id do pedido e da semente: o mesmo pedido cai sempre
    no mesmo grupo, em qualquer máquina e em qualquer ordem de chegada. Trocar
    a semente gera um novo sorteio independente (para um novo experimento).
    """
    if not 0 < treatment_share < 1:
        raise ValueError("treatment_share precisa estar entre 0 e 1.")
    digest = hashlib.sha256(f"{seed}:{order_id}".encode()).hexdigest()
    bucket = int(digest[:12], 16) % BUCKETS
    return "treatment" if bucket < treatment_share * BUCKETS else "control"
