"""
Quick manual retrieval test after ingestion.

Usage:
    python scripts/test_retrieval.py "Wat is de rol van AI in software ontwikkeling?"
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sogyo_chatbot.retrieval import retrieve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", default="Wat is de filosofie achter Sogyo?")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    print(f"Query: {args.query}\n")
    hits = retrieve(args.query, top_k=args.k)

    if not hits:
        print("Geen resultaten. Heb je al een ingest gedaan?")
        return

    for i, hit in enumerate(hits, 1):
        meta = hit["metadata"]
        print(f"[{i}] {meta.get('title', '(no title)')}")
        print(f"    Source: {meta.get('source')} | {meta.get('url')}")
        print(f"    Distance: {hit['distance']:.4f}")
        print(f"    Text: {hit['text'][:280]}...\n")


if __name__ == "__main__":
    main()
