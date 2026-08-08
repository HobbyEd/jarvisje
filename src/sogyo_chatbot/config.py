"""Simple configuration for the Sogyo Chatbot MVP.

Lightweight: pydantic + environment variables (+ optional .env file).

Secrets (ADR-011): never hardcode tokens/passwords here. Load from environment
or a gitignored `.env` file. See `.env.example` and ADR-011.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from pydantic import BaseModel, Field

try:
    from dotenv import load_dotenv as _dotenv_load
except ImportError:  # requirements include python-dotenv; fallback parser below
    _dotenv_load = None  # type: ignore[assignment]


def _parse_env_file(path: Path, *, override: bool = False) -> None:
    """Minimal KEY=VALUE loader (no export, no multiline). Does not override by default."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:].strip()
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'").strip('"')
        if not key:
            continue
        if not override and key in os.environ:
            continue
        os.environ[key] = val


def _load_env_files() -> None:
    """Load gitignored .env files into os.environ (does not override existing env)."""
    here = Path(__file__).resolve()
    # src/sogyo_chatbot/config.py → repo root (local) or /app (container layout)
    candidates = [
        here.parents[2] / ".env",  # .../project/.env or /app/.env
        here.parents[1] / ".env",
        Path.cwd() / ".env",
    ]
    seen: set[Path] = set()
    for path in candidates:
        try:
            resolved = path.resolve()
        except Exception:
            continue
        if resolved in seen or not path.is_file():
            continue
        seen.add(resolved)
        if _dotenv_load is not None:
            _dotenv_load(path, override=False)
        else:
            _parse_env_file(path, override=False)
    if _dotenv_load is not None:
        _dotenv_load(override=False)


_load_env_files()


def _env_str(*keys: str, default: str = "") -> str:
    for key in keys:
        val = os.getenv(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return default


def _env_int(key: str, default: int) -> int:
    raw = os.getenv(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


class Settings(BaseModel):
    # Base paths
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_dir: Path = Field(default_factory=lambda: Path("data"))
    raw_dir: Path = Field(default_factory=lambda: Path("data/raw"))
    chroma_persist_dir: Path = Field(default_factory=lambda: Path("data/chroma"))

    # Embedding model (local via sentence-transformers)
    embedding_model: str = "BAAI/bge-m3"

    # Chunking (simple but effective for MVP)
    chunk_size: int = 800
    chunk_overlap: int = 150

    embedding_batch_size: int = 32

    # Ingestion politeness
    request_timeout: float = 15.0
    request_delay_seconds: float = 0.8
    user_agent: str = "SogyoChatbot/0.1 (+https://sogyo.nl; educational bot)"

    sources: List[str] = [
        "https://sogyo.nl",
        "https://jeroenteunisse.nl",
        "https://edwinvandillen.nl",
        "https://augmentedorganisation.nl",
        "https://intentdriven.nl",
        "https://augmentedengineering.nl",
    ]

    max_pages_per_domain: int = Field(
        default_factory=lambda: _env_int("MAX_PAGES_PER_DOMAIN", 500)
    )
    hard_cap_pages_per_domain: int = Field(
        default_factory=lambda: _env_int("HARD_CAP_PAGES_PER_DOMAIN", 2000)
    )
    ingest_batch_size: int = Field(
        default_factory=lambda: _env_int("INGEST_BATCH_SIZE", 20)
    )

    # ADR-011: required for UI/API start|stop — from env / .env only, no code default
    ingest_token: str = Field(
        default_factory=lambda: _env_str("INGEST_TOKEN", "INDEX_TOKEN")
    )

    collection_name: str = "sogyo_knowledge"

    llm_base_url: str = Field(
        default_factory=lambda: _env_str("LLM_BASE_URL", default="http://127.0.0.1:11434/v1")
    )
    llm_model: str = Field(
        default_factory=lambda: _env_str("LLM_MODEL", default="gemma3:4b")
    )
    llm_timeout: float = Field(default_factory=lambda: _env_float("LLM_TIMEOUT", 180.0))
    llm_temperature: float = Field(default_factory=lambda: _env_float("LLM_TEMPERATURE", 0.2))
    llm_max_tokens: int = Field(default_factory=lambda: _env_int("LLM_MAX_TOKENS", 1200))

    embedding_api_base: str = Field(
        default_factory=lambda: _env_str("EMBEDDING_API_BASE", default="")
    )

    def ensure_dirs(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_persist_dir.mkdir(parents=True, exist_ok=True)

    @property
    def ingest_token_configured(self) -> bool:
        return bool(self.ingest_token)


# Global settings instance
settings = Settings()
settings.ensure_dirs()
