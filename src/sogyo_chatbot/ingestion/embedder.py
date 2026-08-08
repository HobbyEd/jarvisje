"""
Embeddings support.

- Local: sentence-transformers (BGE-M3 etc) on GPU/CPU
- Remote: call OpenAI-compatible /v1/embeddings on DGX (recommended on heavy hardware)

When EMBEDDING_API_BASE is set, embeddings are outsourced to the DGX (no local model needed in container).
"""
from __future__ import annotations

import gc
import os
from typing import List

import httpx
import torch
from sentence_transformers import SentenceTransformer

from ..config import settings

# Reduce thread counts for CPU torch/sentence-transformers early.
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")

_embedder: SentenceTransformer | None = None


def get_embedder() -> SentenceTransformer:
    """Singleton-style embedder (only used for local mode)."""
    global _embedder
    if _embedder is None:
        device_pref = os.getenv("EMBEDDING_DEVICE", "auto").lower()
        if device_pref == "cpu":
            device = "cpu"
        elif device_pref == "cuda":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Loading embedding model: {settings.embedding_model} on {device} ...")
        _embedder = SentenceTransformer(settings.embedding_model, device=device)

        if device == "cuda":
            print("  → Using NVIDIA GPU for embeddings (optimal).")
            try:
                torch.backends.cuda.matmul.allow_tf32 = True
                torch.set_float32_matmul_precision("medium")
            except Exception:
                pass
        else:
            try:
                torch.set_num_threads(4)
            except Exception:
                pass
    return _embedder


def _embed_remote(texts: List[str], batch_size: int = 64) -> List[List[float]]:
    """Call remote embeddings API (vLLM /v1/embeddings or compatible)."""
    base = settings.embedding_api_base.rstrip("/")
    url = f"{base}/embeddings"
    all_embs: List[List[float]] = []

    with httpx.Client(timeout=60.0) as client:
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp = client.post(
                url,
                json={
                    "model": settings.embedding_model,
                    "input": batch,
                    "encoding_format": "float",
                },
            )
            resp.raise_for_status()
            data = resp.json()["data"]
            # preserve order
            sorted_items = sorted(data, key=lambda x: x.get("index", 0))
            for item in sorted_items:
                all_embs.append(item["embedding"])

    return all_embs


def embed_chunks(texts: List[str], batch_size: int | None = None) -> List[List[float]]:
    """Return list of embedding vectors for the given texts.

    If EMBEDDING_API_BASE is set, embeddings are outsourced to the DGX
    (no local heavy model required in the container).
    """
    if getattr(settings, "embedding_api_base", ""):
        bs = batch_size or getattr(settings, "embedding_batch_size", 64)
        return _embed_remote(texts, bs)

    # Local mode (original behavior)
    model = get_embedder()
    is_cuda = torch.cuda.is_available()

    default_bs = 128 if is_cuda else getattr(settings, "embedding_batch_size", 16)
    bs = batch_size or default_bs

    all_embeddings: List[List[float]] = []
    for i in range(0, len(texts), bs):
        batch = texts[i : i + bs]
        embs = model.encode(
            batch,
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True,
            batch_size=bs,
        )
        all_embeddings.extend(embs.tolist())

        if (i // bs) % 3 == 0:
            gc.collect()
            if is_cuda:
                try:
                    torch.cuda.empty_cache()
                except Exception:
                    pass

    return all_embeddings
