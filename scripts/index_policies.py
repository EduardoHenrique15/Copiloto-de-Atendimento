"""Indexa as políticas fictícias no ChromaDB local (CHROMA_DIR), do zero.

Uso: python scripts/index_policies.py
Depois, para testar a busca sem chamar o LLM:
     python scripts/index_policies.py --query "não recebi meu pedido" --category nao_recebido
"""

import argparse
from pathlib import Path

from copiloto.ai.copilot.policies import load_policies
from copiloto.ai.copilot.retrieve import PolicyRetriever
from copiloto.ai.triage.embeddings_lr import SentenceTransformerEmbedder
from copiloto.core.config import get_settings
from copiloto.integrations.vectorstore import ChromaVectorStore

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--query")
    parser.add_argument("--category")
    args = parser.parse_args()

    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    chunks = load_policies(ROOT / "policies")
    if args.query:
        retriever = PolicyRetriever(chunks, embedder, ChromaVectorStore(settings.chroma_dir))
        for chunk in retriever.retrieve(args.query, args.category, settings.rag_top_k):
            print(f"{chunk.id}: {chunk.text[:90]}...")
        return
    retriever = PolicyRetriever(
        chunks, embedder, ChromaVectorStore(settings.chroma_dir, reset=True)
    )
    print(
        f"{retriever.index()} trechos de {len({c.policy_id for c in chunks})} políticas indexados."
    )


if __name__ == "__main__":
    main()
