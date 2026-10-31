import numpy as np

from copiloto.integrations.vectorstore import ChromaVectorStore, InMemoryVectorStore


def _check(store):
    store.add(["a", "b"], np.array([[1.0, 0.0], [0.0, 1.0]]), [{"p": "1"}, {"p": "2"}])
    hits = store.query(np.array([0.9, 0.1]), k=2)
    assert [h.id for h in hits] == ["a", "b"]
    assert hits[0].score > hits[1].score
    assert hits[0].metadata == {"p": "1"}
    assert store.count() == 2


def test_in_memory_store():
    _check(InMemoryVectorStore())


def test_chroma_store_persists(tmp_path):
    _check(ChromaVectorStore(tmp_path / "chroma"))
    assert ChromaVectorStore(tmp_path / "chroma").count() == 2
    assert ChromaVectorStore(tmp_path / "chroma", reset=True).count() == 0
