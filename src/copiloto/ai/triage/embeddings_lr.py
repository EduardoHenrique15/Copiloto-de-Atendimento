"""Triagem com embeddings locais (sentence-transformers) + regressão logística.

Treinada no conjunto prata (rótulos do LLM). Roda em CPU, sem custo por chamada.
"""

import time
from pathlib import Path
from typing import Protocol

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression

from copiloto.ai.triage.base import TriageResult

SEED = 42


class Embedder(Protocol):
    name: str

    def encode(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbedder:
    """Modelo multilíngue local. O import é feito só aqui, para os testes
    (que usam um embedder falso) não precisarem do torch."""

    def __init__(self, model_name: str, batch_size: int = 64) -> None:
        from sentence_transformers import SentenceTransformer

        self.name = model_name
        self.batch_size = batch_size
        self._model = SentenceTransformer(model_name, device="cpu")

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(
            texts,
            batch_size=self.batch_size,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )


class EmbeddingsLRTriager:
    """Regressão logística multinomial sobre embeddings normalizados.

    `class_weight="balanced"` compensa categorias raras (ex.: atendimento_vendedor).
    A confiança é a maior probabilidade prevista.
    """

    name = "embeddings_lr"

    def __init__(self, embedder: Embedder, c: float = 4.0) -> None:
        self.embedder = embedder
        self.model = LogisticRegression(
            C=c, max_iter=3000, class_weight="balanced", random_state=SEED
        )

    def fit(self, texts: list[str], labels: list[str]) -> "EmbeddingsLRTriager":
        self.model.fit(self.embedder.encode(texts), labels)
        return self

    def predict_proba(self, texts: list[str]) -> np.ndarray:
        return self.model.predict_proba(self.embedder.encode(texts))

    @property
    def classes(self) -> list[str]:
        return list(self.model.classes_)

    def predict(self, text: str) -> TriageResult:
        start = time.perf_counter()
        proba = self.predict_proba([text])[0]
        best = int(np.argmax(proba))
        return TriageResult(
            category=self.classes[best],
            confidence=float(proba[best]),
            latency_ms=(time.perf_counter() - start) * 1000,
        )

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump({"embedder_name": self.embedder.name, "model": self.model}, path)

    @classmethod
    def load(cls, path: Path, embedder: Embedder | None = None) -> "EmbeddingsLRTriager":
        data = joblib.load(path)
        triager = cls(embedder or SentenceTransformerEmbedder(data["embedder_name"]))
        triager.model = data["model"]
        return triager
