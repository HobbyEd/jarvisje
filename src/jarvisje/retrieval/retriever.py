"""
Basic retriever used by the chatbot.

Chroma similarity search plus a hard host allowlist (ADR-012).
"""
from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse

from ..config import settings
from ..ingestion.embedder import get_embedder
from ..ingestion.vector_store import get_chroma_store, invalidate_collection_cache


def _host(value: str) -> str:
    return urlparse(value).netloc.lower().lstrip("www.") if "://" in value else value.lower().lstrip("www.")


def _is_allowed_hit(meta: Dict[str, Any]) -> bool:
    allowed = set(settings.allowed_hosts())
    url = str(meta.get("url") or "")
    source = str(meta.get("source") or "")
    if url and _host(url) in allowed:
        return True
    if source and source.lower().lstrip("www.") in allowed:
        return True
    return False


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
    fetch_k = max(top_k * 3, top_k)

    query_kwargs: Dict[str, Any] = {
        "query_embeddings": q_vec,
        "n_results": fetch_k,
        "include": ["documents", "metadatas", "distances"],
    }
    source_values = settings.chroma_source_values()
    if source_values:
        query_kwargs["where"] = {"source": {"$in": source_values}}

    def _query(col: Any, with_filter: bool) -> Any:
        kwargs = dict(query_kwargs)
        if not with_filter:
            kwargs.pop("where", None)
        return col.query(**kwargs)

    try:
        results = _query(collection, with_filter=True)
    except Exception as exc:
        msg = str(exc).lower()
        if "does not exist" in msg or "not found" in msg:
            invalidate_collection_cache()
            try:
                collection = get_chroma_store()
                results = _query(collection, with_filter=True)
            except Exception:
                return []
        else:
            try:
                results = _query(collection, with_filter=False)
            except Exception:
                invalidate_collection_cache()
                return []

    hits: List[Dict[str, Any]] = []
    if not results["documents"] or not results["documents"][0]:
        return hits

    for text, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        meta = meta or {}
        if not _is_allowed_hit(meta):
            continue
        hits.append(
            {
                "text": text,
                "metadata": meta,
                "distance": dist,
            }
        )
        if len(hits) >= top_k:
            break
    return hits


def nearest_hit(text: str) -> tuple[float | None, str | None]:
    """Best cosine distance of this text, and the title of that chunk."""
    cleaned = (text or "").strip()
    if not cleaned:
        return None, None
    hits = retrieve(cleaned, top_k=1)
    if not hits:
        return None, None
    meta = hits[0].get("metadata") or {}
    title = str(meta.get("title") or "").strip() or None
    distance = hits[0].get("distance")
    return (float(distance) if distance is not None else None), title
