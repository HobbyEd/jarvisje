"""
Chroma vector store wrapper (MVP: start with Chroma, migrate path to Qdrant documented).

Provides:
- get collection
- upsert list of chunk documents
- basic similarity search (for testing in Fase 0/1)
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api.models.Collection import Collection

from ..config import settings

_client: chromadb.PersistentClient | None = None
_collection: Collection | None = None


def get_chroma_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=str(settings.chroma_persist_dir))
    return _client


def _get_collection_name() -> str:
    """Make collection name model-specific to prevent dimension mismatch errors
    when switching embedding models (e.g. 384 vs 1024)."""
    model = settings.embedding_model
    safe = model.replace("/", "_").replace("-", "_").replace(".", "_")
    return f"sogyo_knowledge_{safe}"


def get_chroma_store() -> Collection:
    """Get (or create) the main collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=_get_collection_name(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _make_id(doc: Dict[str, Any]) -> str:
    url = doc.get("url", "unknown")
    chunk_id = doc.get("chunk_id", 0)
    return f"{url}::chunk-{chunk_id}"


def get_indexed_page_index() -> Dict[str, Dict[str, str]]:
    """Return map of cleaned URL → {lastmod, source} for incremental ingest.

    One entry per unique page URL already present in Chroma (any chunk).
    lastmod prefers stored lastmod, else article_date.
    """
    from urllib.parse import urlparse

    def _clean(url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme == "http":
            parsed = parsed._replace(scheme="https")
        return parsed._replace(fragment="").geturl().rstrip("/")

    collection = get_chroma_store()
    try:
        res = collection.get(include=["metadatas"])
    except Exception:
        return {}

    index: Dict[str, Dict[str, str]] = {}
    for m in res.get("metadatas") or []:
        if not m:
            continue
        raw_url = m.get("url")
        if not raw_url:
            continue
        url = _clean(str(raw_url))
        lm = (m.get("lastmod") or m.get("article_date") or "").strip()
        src = (m.get("source") or "").strip()
        prev = index.get(url)
        if prev is None:
            index[url] = {"lastmod": lm, "source": src}
        elif lm and (not prev.get("lastmod") or lm > prev["lastmod"]):
            index[url] = {"lastmod": lm, "source": src or prev.get("source", "")}
    return index


def upsert_chunks(chunk_docs: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
    """
    Upsert chunk documents + their embeddings into Chroma.

    Expects parallel lists.
    """
    if not chunk_docs:
        return 0

    collection = get_chroma_store()

    ids = [_make_id(d) for d in chunk_docs]
    texts = [d["text"] for d in chunk_docs]
    metadatas = [
        {
            "url": d.get("url"),
            "title": d.get("title"),
            "source": d.get("source"),
            "chunk_id": d.get("chunk_id"),
            "ingested_at": d.get("ingested_at") or "",
            "article_date": d.get("article_date") or d.get("lastmod") or "",
            "lastmod": d.get("lastmod") or "",
        }
        for d in chunk_docs
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(ids)


def query_collection(query_text: str, n_results: int = 5) -> list[dict]:
    """Simple query helper (mainly for Fase 0 testing).
    Returns list of {"text": ..., "metadata": {...}, "distance": ...}
    """
    collection = get_chroma_store()
    from .embedder import get_embedder

    model = get_embedder()
    q_emb = model.encode([query_text], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=q_emb,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[dict] = []
    docs = results.get("documents") or [[]]
    metas = results.get("metadatas") or [[]]
    dists = results.get("distances") or [[]]
    for text, meta, dist in zip(docs[0], metas[0], dists[0]):
        hits.append({
            "text": text,
            "metadata": meta or {},
            "distance": dist,
        })
    return hits
