"""Busca dos trechos de política mais relevantes para uma reclamação."""

from copiloto.ai.copilot.policies import PolicyChunk
from copiloto.ai.taxonomy import BY_KEY
from copiloto.ai.triage.embeddings_lr import Embedder
from copiloto.integrations.vectorstore import VectorStore


class PolicyRetriever:
    def __init__(self, chunks: list[PolicyChunk], embedder: Embedder, store: VectorStore) -> None:
        self.chunks = {c.id: c for c in chunks}
        self.embedder = embedder
        self.store = store

    def index(self) -> int:
        """Indexa título, seção e texto de cada trecho. Devolve quantos foram indexados."""
        chunks = list(self.chunks.values())
        texts = [f"{c.policy_title}. {c.section}. {c.text}" for c in chunks]
        self.store.add(
            [c.id for c in chunks],
            self.embedder.encode(texts),
            [{"policy_id": c.policy_id} for c in chunks],
        )
        return len(chunks)

    def retrieve(self, complaint: str, category: str | None, k: int) -> list[PolicyChunk]:
        """A consulta junta a descrição da categoria (da triagem) ao texto do cliente."""
        hint = BY_KEY[category].description if category in BY_KEY else ""
        vector = self.embedder.encode([f"{hint} {complaint}".strip()])[0]
        return [self.chunks[h.id] for h in self.store.query(vector, k) if h.id in self.chunks]
