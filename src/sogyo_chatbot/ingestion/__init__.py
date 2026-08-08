"""Ingestion pipeline: scrape → extract → chunk → embed → store."""
from .scraper import scrape_domain, scrape_all_sources
from .chunker import chunk_text, chunk_documents
from .embedder import get_embedder, embed_chunks
from .vector_store import get_chroma_store, upsert_chunks

__all__ = [
    "scrape_domain",
    "chunk_text",
    "chunk_documents",
    "get_embedder",
    "embed_chunks",
    "get_chroma_store",
    "upsert_chunks",
]
