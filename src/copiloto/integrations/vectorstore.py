"""Armazenamento vetorial dos trechos de política: ChromaDB local ou em memória."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class Hit:
    id: str
    score: float  # similaridade de cosseno (1 = idêntico)
    metadata: dict


class VectorStore(Protocol):
    def add(self, ids: list[str], vectors: np.ndarray, metadatas: list[dict]) -> None: ...

    def query(self, vector: np.ndarray, k: int) -> list[Hit]: ...

    def count(self) -> int: ...


class InMemoryVectorStore:
    """Busca exata por cosseno em memória. Suficiente para dezenas de trechos e para testes."""

    def __init__(self) -> None:
        self._ids: list[str] = []
        self._meta: list[dict] = []
        self._vectors = np.zeros((0, 0))

    def add(self, ids: list[str], vectors: np.ndarray, metadatas: list[dict]) -> None:
        vectors = np.asarray(vectors, dtype=float)
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        vectors = vectors / np.where(norms == 0, 1, norms)
        self._vectors = vectors if not self._ids else np.vstack([self._vectors, vectors])
        self._ids += ids
        self._meta += metadatas

    def query(self, vector: np.ndarray, k: int) -> list[Hit]:
        v = np.asarray(vector, dtype=float)
        v = v / (np.linalg.norm(v) or 1)
        scores = self._vectors @ v
        order = np.argsort(-scores, kind="stable")[:k]
        return [Hit(self._ids[i], float(scores[i]), self._meta[i]) for i in order]

    def count(self) -> int:
        return len(self._ids)


class ChromaVectorStore:
    """ChromaDB persistente em disco (CHROMA_DIR). Os vetores vêm do nosso embedder."""

    COLLECTION = "politicas"

    def __init__(self, path: Path, reset: bool = False) -> None:
        import chromadb

        self._client = chromadb.PersistentClient(path=str(path))
        if reset and self.COLLECTION in [c.name for c in self._client.list_collections()]:
            self._client.delete_collection(self.COLLECTION)
        self._col = self._client.get_or_create_collection(
            self.COLLECTION, metadata={"hnsw:space": "cosine"}, embedding_function=None
        )

    def add(self, ids: list[str], vectors: np.ndarray, metadatas: list[dict]) -> None:
        self._col.add(ids=ids, embeddings=np.asarray(vectors).tolist(), metadatas=metadatas)

    def query(self, vector: np.ndarray, k: int) -> list[Hit]:
        r = self._col.query(query_embeddings=[np.asarray(vector).tolist()], n_results=k)
        return [
            Hit(i, 1.0 - float(d), m)
            for i, d, m in zip(r["ids"][0], r["distances"][0], r["metadatas"][0], strict=True)
        ]

    def count(self) -> int:
        return self._col.count()
