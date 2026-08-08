"""Simple configuration for the Sogyo Chatbot MVP.

Lightweight: uses pydantic + environment variables.
Production defaults point at local Ollama on the app host (.15):
  LLM_BASE_URL=http://ollama:11434/v1   # inside compose network
  LLM_MODEL=gemma3:4b
  EMBEDDING_DEVICE=cpu                  # set in compose; see embedder.py

Override for local dev, e.g.:
  LLM_BASE_URL=http://192.168.165.15:11434/v1
  LLM_MODEL=gemma3:4b
Other OpenAI-compatible endpoint example:
  LLM_BASE_URL=http://127.0.0.1:11434/v1
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field


class Settings(BaseModel):
    # Base paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    raw_dir: Path = Field(default_factory=lambda: Path("data/raw"))
    chroma_persist_dir: Path = Field(default_factory=lambda: Path("data/chroma"))

    # Embedding model (local via sentence-transformers)
    # Good multilingual options: "BAAI/bge-m3" or "intfloat/multilingual-e5-large"
    embedding_model: str = "BAAI/bge-m3"

    # Chunking (simple but effective for MVP)
    chunk_size: int = 800          # characters (approx ~150-200 tokens)
    chunk_overlap: int = 150

    # Embedding batching
    # GPU (CUDA) uses much larger batches internally; this is mainly the CPU fallback.
    embedding_batch_size: int = 32

    # Ingestion politeness
    request_timeout: float = 15.0
    request_delay_seconds: float = 0.8
    user_agent: str = "SogyoChatbot/0.1 (+https://sogyo.nl; educational bot)"

    # Sources for broad MVP coverage
    sources: List[str] = [
        "https://sogyo.nl",
        "https://jeroenteunisse.nl",
        "https://edwinvandillen.nl",
        "https://augmentedorganisation.nl",
        "https://intentdriven.nl",
        "https://augmentedengineering.nl",
    ]

    # Max content pages per domain (safety cap). UI may raise this further.
    # Sitemap URLs are prioritized so blog posts are not starved by nav/pagination.
    # 0 or negative = use hard_cap_pages_per_domain only.
    max_pages_per_domain: int = int(os.getenv("MAX_PAGES_PER_DOMAIN", "500"))
    hard_cap_pages_per_domain: int = int(os.getenv("HARD_CAP_PAGES_PER_DOMAIN", "2000"))

    # Upsert/embed batch size during live ingest (keeps UI fresh + limits memory)
    ingest_batch_size: int = int(os.getenv("INGEST_BATCH_SIZE", "20"))

    # Token required to start/stop ingestion (UI field + backend check)
    ingest_token: str = os.getenv(
        "INGEST_TOKEN",
        "eyJhIDAHHEIEHBXTWLANDGR3A7HA5ALO8OL0JF",
    )

    # Chroma collection name (overridden at runtime to be model-specific)
    collection_name: str = "sogyo_knowledge"

    # LLM (OpenAI-compatible: Ollama, vLLM, …)
    # Defaults match production Ollama on the same host (override in compose/env).
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1")
    llm_model: str = os.getenv("LLM_MODEL", "gemma3:4b")
    llm_timeout: float = float(os.getenv("LLM_TIMEOUT", "180.0"))
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    llm_max_tokens: int = int(os.getenv("LLM_MAX_TOKENS", "1200"))

    # Embeddings: local BGE-M3 (device via EMBEDDING_DEVICE=cpu|cuda|auto in embedder)
    # Or remote OpenAI-compatible /embeddings: set EMBEDDING_API_BASE
    embedding_api_base: str = os.getenv("EMBEDDING_API_BASE", "")

    def ensure_dirs(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_dirs()
