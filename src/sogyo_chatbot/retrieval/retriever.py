"""
Basic retriever used by the chatbot.

For Fase 0 this is mainly a thin wrapper around Chroma + embeddings.
Later we will add:
- query rewriting / expansion
- metadata filtering
- re-ranking (optional)
"""
from __future__ import annotations

from typing import Any, Dict, List

from ..ingestion.embedder import get_embedder
from ..ingestion.vector_store import get_chroma_store


def retrieve(query: str, top_k: int = 6) -> List[Dict[str, Any]]:
    """
    Retrieve relevant chunks for a query.

    Returns list of dicts with keys:
      - text
      - metadata (url, title, source, chunk_id)
      - distance (lower is better)
    """
    collection = get_chroma_store()
    embedder = get_embedder()

    q_vec = embedder.encode([query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=q_vec,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    hits: List[Dict[str, Any]] = []
    if not results["documents"] or not results["documents"][0]:
        return hits

    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append(
            {
                "text": text,
                "metadata": meta or {},
                "distance": dist,
            }
        )
    return hits
