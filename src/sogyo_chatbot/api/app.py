"""FastAPI application with SSE streaming chat."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator, Dict, List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ..chat.models import Citation
from ..chat.orchestrator import ChatOrchestrator, ChatResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Preload the embedding model at startup. BGE-M3 is large (~2GB) and the first
    # retrieval (/chat or /sources with retrieval) will otherwise block while
    # downloading + loading (can take 30-90s on first run, even with GPU).
    # Preloading makes the first user request fast and avoids timeouts.
    from ..config import settings
    from ..ingestion.embedder import get_embedder
    if settings.embedding_api_base:
        print("Using remote embeddings API; skipping local model preload.")
    else:
        print("Preloading embedding model at startup (this may take a moment)...")
        get_embedder()
    yield


app = FastAPI(title="Sogyo Kennis Chatbot API", lifespan=lifespan)

# Serve static assets from the web/ directory (e.g. logo)
# This allows /static/sogyo-30-jaar.png etc.
app.mount("/static", StaticFiles(directory="web"), name="static")

# CORS for testing from other ports/domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local testing; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory sessions for MVP (simple)
_sessions: Dict[str, ChatOrchestrator] = {}


class ChatRequest(BaseModel):
    session_id: str = "default"
    message: str
    history: List[Dict[str, str]] | None = None  # optional override


class IngestStartRequest(BaseModel):
    """Body for POST /ingest/start — token required."""
    token: str
    max_pages: int | None = None  # None = config default; 0 = hard cap (full site)
    reset: bool = False


class IngestStopRequest(BaseModel):
    token: str


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _stream_chat(req: ChatRequest) -> AsyncGenerator[str, None]:
    orchestrator = _sessions.setdefault(req.session_id, ChatOrchestrator())

    # Get response (the heavy lifting happens here)
    try:
        response: ChatResponse = orchestrator.chat(req.message, history=req.history)
    except Exception as e:
        error_msg = str(e)
        if "LLM call failed" in error_msg or "not reachable" in error_msg.lower():
            error_msg = (
                "LLM endpoint is not reachable. Check Ollama (e.g. gemma3:4b on :11434) "
                "and LLM_BASE_URL / LLM_MODEL env."
            )
        yield _format_sse("error", {"message": error_msg})
        return

    # Stream the answer in chunks (simulated token streaming for MVP)
    answer = response.answer
    chunk_size = 40
    for i in range(0, len(answer), chunk_size):
        part = answer[i : i + chunk_size]
        yield _format_sse("delta", {"content": part})

    # Send final payload with citations + hints
    final = {
        "answer": answer,
        "citations": [c.model_dump() for c in response.citations],
        "hints": response.hints,
        "role_context": response.role_context,
    }
    yield _format_sse("final", final)


@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    """Streaming chat endpoint using Server-Sent Events."""
    return StreamingResponse(
        _stream_chat(req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/chat/sync")
async def chat_sync(req: ChatRequest):
    """Non-streaming test endpoint. Returns full structured response directly (for curl/Python testing)."""
    orchestrator = _sessions.setdefault(req.session_id, ChatOrchestrator())
    try:
        response: ChatResponse = orchestrator.chat(req.message, history=req.history)
        return {
            "answer": response.answer,
            "citations": [c.model_dump() for c in response.citations],
            "hints": response.hints,
            "role_context": response.role_context,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": str(e),
                "fallback": "LLM may not be reachable or response was invalid.",
            }
        )


@app.get("/test-retrieval")
async def test_retrieval(query: str, top_k: int = 5):
    """Test endpoint to inspect retrieval only (no LLM call). Useful for debugging content."""
    from ..retrieval.retriever import retrieve
    hits = retrieve(query, top_k=top_k)
    return {
        "query": query,
        "hits": [
            {
                "text": h["text"][:500] + "..." if len(h["text"]) > 500 else h["text"],
                "metadata": h["metadata"],
                "distance": h.get("distance"),
            }
            for h in hits
        ]
    }


@app.get("/health")
async def health():
    from sogyo_chatbot.config import settings
    return {
        "status": "ok",
        "embedding": settings.embedding_model,
        "llm_base_url": settings.llm_base_url,
        "llm_model": settings.llm_model,
    }


@app.get("/sources")
async def sources():
    """Metadata overview of indexed sources.

    Per source:
    - page_count
    - last_ingested_at — when we last wrote chunks (ingest run)
    - newest_article_date — newest article/publish/lastmod date in the store
    """
    from collections import defaultdict
    from ..ingestion.vector_store import get_chroma_store

    collection = get_chroma_store()
    try:
        res = collection.get(include=["metadatas"])
        metas = res.get("metadatas") or []
    except Exception as e:
        return {"sources": [], "total_unique_pages": 0, "error": str(e)}

    stats: dict = defaultdict(
        lambda: {
            "urls": set(),
            "last_ingested_at": None,
            "newest_article_date": None,
        }
    )

    for m in metas:
        if not m:
            continue
        src = m.get("source") or "unknown"
        url = m.get("url")
        if url:
            stats[src]["urls"].add(url)
        ts = m.get("ingested_at") or ""
        if ts:
            cur = stats[src]["last_ingested_at"]
            if not cur or ts > cur:
                stats[src]["last_ingested_at"] = ts
        article = (m.get("article_date") or m.get("lastmod") or "").strip()
        if article:
            cur_a = stats[src]["newest_article_date"]
            if not cur_a or article > cur_a:
                stats[src]["newest_article_date"] = article

    sources_list = []
    for src in sorted(stats.keys()):
        data = stats[src]
        sources_list.append({
            "source": src,
            "page_count": len(data["urls"]),
            "last_updated": data["last_ingested_at"],  # backward compatible
            "last_ingested_at": data["last_ingested_at"],
            "newest_article_date": data["newest_article_date"],
        })

    try:
        from ..config import settings
        configured = [
            s.replace("https://", "").replace("http://", "").rstrip("/")
            for s in settings.sources
        ]
    except Exception:
        configured = []

    return {
        "sources": sources_list,
        "total_unique_pages": sum(s["page_count"] for s in sources_list),
        "configured_sources": configured,
        "ingest_requires_token": True,
    }



def _check_ingest_token(token: str | None) -> bool:
    from sogyo_chatbot.config import settings

    expected = (settings.ingest_token or "").strip()
    if not expected:
        return False
    return (token or "").strip() == expected


def _spawn_ingest_worker(max_pages: int | None, reset: bool) -> subprocess.Popen:
    """Start ADR-010 worker in a separate process (same image/code)."""
    cmd = [sys.executable, "-m", "sogyo_chatbot.ingestion.worker"]
    if max_pages is not None:
        cmd.extend(["--max-pages", str(max_pages)])
    if reset:
        cmd.append("--reset")

    env = os.environ.copy()
    src = str(Path(__file__).resolve().parents[2])  # .../src
    prev = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = src if not prev else f"{src}{os.pathsep}{prev}"

    from sogyo_chatbot.config import settings

    settings.ensure_dirs()
    log_path = Path(settings.data_dir) / "ingest_worker.log"
    log_f = open(log_path, "a", encoding="utf-8")  # noqa: SIM115 — owned by Popen
    log_f.write(f"\n--- spawn {' '.join(cmd)} ---\n")
    log_f.flush()

    return subprocess.Popen(
        cmd,
        env=env,
        cwd=str(Path.cwd()),
        start_new_session=True,
        stdout=log_f,
        stderr=subprocess.STDOUT,
    )


@app.post("/ingest/start")
async def start_ingest(req: IngestStartRequest):
    """Start indexering in a separate worker process (ADR-010). Token required."""
    from sogyo_chatbot.ingestion.status import (
        clear_stop_flag,
        is_worker_running,
        utc_now_iso,
        write_status,
    )

    if not _check_ingest_token(req.token):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Ongeldig of ontbrekend indexeringstoken.",
            },
        )

    if is_worker_running():
        return {"status": "error", "message": "Er loopt al een indexering."}

    clear_stop_flag()
    write_status(
        {
            "status": "running",
            "progress": 1,
            "message": "Worker starten… (apart proces)",
            "started_at": utc_now_iso(),
            "finished_at": None,
            "error": None,
            "stop_requested": False,
            "pages_scraped": 0,
            "chunks_indexed": 0,
            "current_source": None,
            "pid": None,
        },
        merge=False,
    )

    try:
        proc = _spawn_ingest_worker(req.max_pages, req.reset)
    except Exception as e:
        write_status(
            {
                "status": "error",
                "message": f"Kon worker niet starten: {e}",
                "error": str(e),
                "finished_at": utc_now_iso(),
            }
        )
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Kon worker niet starten: {e}"},
        )

    # Do not write proc.pid into shared status — only the worker sets pid after
    # acquiring the lock (avoids double-spawn races overwriting the real worker pid).
    write_status({"message": "Indexering loopt in aparte worker…"})
    return {
        "status": "started",
        "message": "Indexering gestart in een apart proces (chat blijft beschikbaar).",
        "max_pages": req.max_pages,
        "reset": req.reset,
        "spawn_pid": proc.pid,
    }


@app.post("/ingest/stop")
async def stop_ingest(req: IngestStopRequest):
    """Ask the worker to stop (stop flag on data volume)."""
    from sogyo_chatbot.ingestion.status import is_worker_running, request_stop

    if not _check_ingest_token(req.token):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Ongeldig of ontbrekend indexeringstoken.",
            },
        )

    if not is_worker_running():
        return {"status": "error", "message": "Geen actieve indexering om te stoppen."}

    request_stop()
    return {"status": "stop_requested", "message": "Stoppen aangevraagd."}


@app.get("/ingest/status")
async def ingest_status():
    """Read-only status from shared status file (ADR-010)."""
    from sogyo_chatbot.ingestion.status import read_status

    return read_status()


# Serve the Sogyo-styled frontend (web/index.html) at root.
# Ensures local run and deployed container give identical UI.
_WEB_DIR = Path(__file__).resolve().parents[3] / "web"
_WEB_INDEX = _WEB_DIR / "index.html"


@app.get("/")
async def index():
    if _WEB_INDEX.exists():
        return FileResponse(str(_WEB_INDEX))
    # Fallback: show a clear error instead of FastAPI's default 404
    return JSONResponse(
        {"error": "web/index.html not found in the image. Make sure the image was built after adding COPY web ./web to the Dockerfile."},
        status_code=500
    )
