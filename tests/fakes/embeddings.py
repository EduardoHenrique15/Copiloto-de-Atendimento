"""Embedder falso e determinístico: saco de palavras com hash, sem modelo nem rede."""

import hashlib
import re

import numpy as np


class FakeEmbedder:
    name = "fake-hash-embedder"

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim
        self.calls = 0

    def encode(self, texts: list[str]) -> np.ndarray:
        self.calls += 1
        out = np.zeros((len(texts), self.dim))
        for i, text in enumerate(texts):
            for word in re.findall(r"\w+", text.lower()):
                h = int(hashlib.md5(word.encode()).hexdigest(), 16)
                out[i, h % self.dim] += 1.0
            norm = np.linalg.norm(out[i])
            if norm:
                out[i] /= norm
        return out
