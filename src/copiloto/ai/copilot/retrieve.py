"""Busca dos trechos de política mais relevantes para uma reclamação."""

from copiloto.ai.copilot.policies import PolicyChunk
from copiloto.ai.taxonomy import BY_KEY
from copiloto.ai.triage.embeddings_lr import Embedder
from copiloto.integrations.vectorstore import VectorStore

# Política principal de cada categoria da triagem. Sem política própria, entra o tom de voz,
# que diz para encaminhar a um especialista.
CATEGORY_POLICIES: dict[str, tuple[str, ...]] = {
    "atraso_entrega": ("atraso-na-entrega",),
    "nao_recebido": ("pedido-nao-recebido",),
    "produto_errado_ou_incompleto": ("produto-errado-ou-incompleto",),
    "produto_defeituoso_ou_qualidade": ("produto-com-defeito",),
    "diferente_do_anuncio": ("troca-e-devolucao",),
    "cancelamento_ou_cobranca": ("cancelamento-e-cobranca",),
    "atendimento_vendedor": ("tom-de-voz",),
    "outro": ("tom-de-voz",),
    "sem_problema": ("tom-de-voz",),
}


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
        """Busca híbrida: todos os trechos da política da categoria, mais `k` da busca vetorial.

        Na avaliação do draft-v1, só a busca vetorial deixou de trazer a política de atraso em
        4 de 8 casos de atraso. A categoria vem da triagem; a busca vetorial cobre o caso de
        a categoria estar errada ou de a reclamação envolver outra política.
        """
        mandatory = [
            c
            for c in self.chunks.values()
            if c.policy_id in CATEGORY_POLICIES.get(category or "", ())
        ]
        hint = BY_KEY[category].description if category in BY_KEY else ""
        vector = self.embedder.encode([f"{hint} {complaint}".strip()])[0]
        seen = {c.id for c in mandatory}
        extra = [
            self.chunks[h.id]
            for h in self.store.query(vector, k + len(seen))
            if h.id in self.chunks and h.id not in seen
        ]
        return mandatory + extra[:k]
