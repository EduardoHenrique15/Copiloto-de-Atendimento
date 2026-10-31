"""Treina a triagem por embeddings + regressão logística no conjunto prata.

Na primeira execução, baixa o modelo de embeddings do HuggingFace (~470 MB).
Saídas: models/triage/embeddings_lr.joblib (fora do git) e
eval/results/triage_embeddings_train.json.

Uso: python scripts/train_triage_embeddings.py
"""

import json
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from copiloto.ai.triage.data import load_silver
from copiloto.ai.triage.embeddings_lr import EmbeddingsLRTriager, SentenceTransformerEmbedder
from copiloto.ai.triage.metrics import quality
from copiloto.core.config import get_settings

ROOT = Path(__file__).resolve().parents[1]
SEED = 42


def main() -> None:
    settings = get_settings()
    silver = load_silver(ROOT / "data" / "labels", settings.duckdb_path)
    texts, labels = silver["text"].tolist(), silver["label"].tolist()

    start = time.perf_counter()
    embedder = SentenceTransformerEmbedder(settings.embedding_model)
    vectors = embedder.encode(texts)
    encode_s = time.perf_counter() - start

    triager = EmbeddingsLRTriager(embedder)
    # Concordância com os rótulos do LLM por validação cruzada no próprio prata.
    # Não é a qualidade real: ela é medida no ouro humano (scripts/evaluate_triage.py).
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    cv_pred = cross_val_predict(triager.model, vectors, labels, cv=folds)
    triager.model.fit(vectors, labels)
    triager.save(ROOT / "models" / "triage" / "embeddings_lr.joblib")

    cv = quality(labels, list(cv_pred))
    report = {
        "embedding_model": settings.embedding_model,
        "n_train": len(texts),
        "embedding_dim": int(np.asarray(vectors).shape[1]),
        "encode_seconds": round(encode_s, 1),
        "cv_agreement_with_llm_labels": {"macro_f1": cv["macro_f1"], "accuracy": cv["accuracy"]},
    }
    out = ROOT / "eval" / "results" / "triage_embeddings_train.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
