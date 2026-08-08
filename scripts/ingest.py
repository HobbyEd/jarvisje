"""
One-shot ingestion script for all sources.

Usage:
    python scripts/ingest.py
    python scripts/ingest.py --max 50          # limit per domain for quick tests
    python scripts/ingest.py --reset           # wipe chroma collection first

De UI (tab Bronnen & Meta-data) kan dezelfde logica triggeren via /ingest/start.
"""
import argparse
from pathlib import Path
import sys

# Ensure src is importable when running from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sogyo_chatbot.config import settings
from sogyo_chatbot.ingestion import (
    chunk_documents,
    embed_chunks,
    get_chroma_store,
    scrape_all_sources,
    upsert_chunks,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=None, help="Max pages per domain (for testing)")
    parser.add_argument("--reset", action="store_true", help="Delete existing collection before ingest")
    args = parser.parse_args()

    from sogyo_chatbot.ingestion.vector_store import get_chroma_client, _get_collection_name

    coll_name = _get_collection_name()

    print("=== Sogyo Chatbot - Fase 0 Ingestion ===")
    print(f"Embedding model : {settings.embedding_model}")
    print(f"Chroma location : {settings.chroma_persist_dir}")
    print(f"Collection      : {coll_name}")
    print(f"Sources         : {len(settings.sources)} domains")
    print()

    if args.reset:
        print("Resetting collection...")
        client = get_chroma_client()
        try:
            client.delete_collection(coll_name)
        except Exception:
            pass
        # Invalidate any cached collection object
        import sogyo_chatbot.ingestion.vector_store as vs
        vs._collection = None
        print(f"Collection '{coll_name}' reset.\n")

    # 1. Scrape
    print("Starting broad scrape...")
    raw_docs = scrape_all_sources(max_pages_per_domain=args.max)
    print(f"Total raw pages extracted: {len(raw_docs)}\n")

    if not raw_docs:
        print("No documents scraped. Exiting.")
        return

    # 2. Chunk
    print("Chunking documents...")
    chunked = chunk_documents(raw_docs)
    print(f"Total chunks: {len(chunked)}\n")

    # 3. Embed
    print("Generating embeddings...")
    texts = [c["text"] for c in chunked]
    embeddings = embed_chunks(texts)

    # 4. Store
    print("Storing in Chroma...")
    inserted = upsert_chunks(chunked, embeddings)
    print(f"Inserted/updated {inserted} chunks in collection '{coll_name}'.\n")

    # Quick sanity query (use our own embeddings for correct dimension)
    print("Running quick test query...")
    from sogyo_chatbot.ingestion.vector_store import query_collection
    test_results = query_collection("Wat is de filosofie van Sogyo?", n_results=3)
    print("Top results for test query:")
    for i, hit in enumerate(test_results):
        meta = hit.get("metadata", {})
        print(f"  {i+1}. {meta.get('title', 'no title')[:80]}")
        print(f"     {meta.get('url')}")
        print(f"     {hit.get('text', '')[:120]}...")
        print()

    print("Ingestion complete.")


if __name__ == "__main__":
    main()
