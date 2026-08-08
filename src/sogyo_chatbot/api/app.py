"""FastAPI application with SSE streaming chat."""
from __future__ import annotations

import json
from typing import List, Dict, AsyncGenerator

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pathlib import Path
from pydantic import BaseModel
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager

from ..chat.orchestrator import ChatOrchestrator, ChatResponse
from ..chat.models import Citation


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

# Simple in-memory state for ingestion progress (MVP)
_ingest_state: dict = {
    "status": "idle",           # idle | running | stopping | stopped | completed | error
    "progress": 0,              # 0-100
    "message": "Geen indexering actief",
    "started_at": None,
    "finished_at": None,
    "current_source": None,
    "error": None,
    "stop_requested": False,
    "pages_scraped": 0,
    "chunks_indexed": 0,
}


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


def _update_ingest_state(**kwargs):
    """Helper to safely update the shared ingest state."""
    global _ingest_state
    _ingest_state.update(kwargs)


def _check_ingest_token(token: str | None) -> bool:
    from sogyo_chatbot.config import settings
    expected = (settings.ingest_token or "").strip()
    if not expected:
        return False
    return (token or "").strip() == expected


async def _run_ingestion_task(max_pages: int | None, reset: bool):
    """Background task: sitemap-first scrape + batched embed/upsert per domain."""
    global _ingest_state

    def _check_stop() -> bool:
        if _ingest_state.get("stop_requested"):
            _update_ingest_state(
                status="stopped",
                message="Indexering gestopt door gebruiker.",
                finished_at=datetime.utcnow().isoformat(),
                current_source=None,
                stop_requested=False,
            )
            return True
        return False

    try:
        _update_ingest_state(
            status="running",
            progress=5,
            message="Indexering gestart — sitemap-first crawl…",
            started_at=datetime.utcnow().isoformat(),
            finished_at=None,
            current_source=None,
            error=None,
            stop_requested=False,
            pages_scraped=0,
            chunks_indexed=0,
        )

        from sogyo_chatbot.ingestion.vector_store import (
            get_chroma_client,
            _get_collection_name,
            get_chroma_store,
        )
        from sogyo_chatbot.ingestion import chunk_documents, embed_chunks, upsert_chunks
        from sogyo_chatbot.ingestion.scraper import scrape_domain
        from sogyo_chatbot.config import settings

        import gc as _gc
        import time as _time

        coll_name = _get_collection_name()

        if reset:
            _update_ingest_state(progress=8, message="Bestaande index wissen…")
            client = get_chroma_client()
            try:
                client.delete_collection(coll_name)
            except Exception:
                pass
            import sogyo_chatbot.ingestion.vector_store as vs

            vs._collection = None
            get_chroma_store()
            await asyncio.sleep(0.3)

        if _check_stop():
            return

        sources = settings.sources
        total_inserted = 0
        total_pages = 0
        batch_size = settings.ingest_batch_size

        def _index_docs_batch(domain: str, docs: list, d_idx: int) -> int:
            """Chunk + embed + upsert one batch; returns chunk count."""
            nonlocal total_inserted, total_pages
            if not docs:
                return 0
            total_pages += len(docs)
            _update_ingest_state(
                message=f"Indexeren batch {domain} ({len(docs)} pagina's)…",
                current_source=domain,
                pages_scraped=total_pages,
            )
            chunked = chunk_documents(docs)
            if not chunked:
                return 0
            texts = [c["text"] for c in chunked]
            embeddings = embed_chunks(texts)
            upsert_bs = 64
            n_total = 0
            for b in range(0, len(chunked), upsert_bs):
                n = upsert_chunks(
                    chunked[b : b + upsert_bs], embeddings[b : b + upsert_bs]
                )
                n_total += n
                total_inserted += n
                _update_ingest_state(chunks_indexed=total_inserted)
                _time.sleep(0.15)
            _gc.collect()
            return n_total

        for idx, start_url in enumerate(sources):
            domain = start_url.replace("https://", "").replace("http://", "").rstrip("/")
            n_sources = max(1, len(sources))
            base_pct = 10 + int((idx / n_sources) * 80)

            pages_before_domain = total_pages

            def _make_progress_cb(d_name: str, d_base: int, pages_before: int):
                def _progress_cb(
                    d_domain: str, scraped_count: int, current_url: str | None = None
                ) -> None:
                    slice_w = max(5, 80 // n_sources)
                    within = min(
                        slice_w - 1,
                        int((scraped_count / max(50, scraped_count + 10)) * slice_w),
                    )
                    live = min(92, d_base + within)
                    cur = d_name
                    if current_url:
                        cur = f"{d_name} — {current_url[:80]}"
                    _update_ingest_state(
                        progress=live,
                        message=f"Scrapen {d_name}… ({scraped_count} artikelen op deze bron)",
                        current_source=cur,
                        pages_scraped=pages_before + scraped_count,
                    )

                return _progress_cb

            def _make_batch_cb(d_name: str, d_idx: int):
                def _batch_cb(docs: list) -> None:
                    if _ingest_state.get("stop_requested"):
                        return
                    _index_docs_batch(d_name, docs, d_idx)

                return _batch_cb

            _update_ingest_state(
                progress=base_pct,
                message=f"Bron {idx + 1}/{n_sources}: {domain} (sitemap-first)…",
                current_source=domain,
            )

            if _check_stop():
                return

            # Live batches: scrape callbacks already upsert so UI/table grows
            scrape_domain(
                start_url,
                max_pages=max_pages,
                progress_callback=_make_progress_cb(domain, base_pct, pages_before_domain),
                batch_callback=_make_batch_cb(domain, idx),
                batch_size=batch_size,
            )

            if _check_stop():
                return
            _time.sleep(0.5)
            _gc.collect()

        if total_pages == 0 and total_inserted == 0:
            _update_ingest_state(
                status="completed",
                progress=100,
                message="Geen documenten gevonden.",
                finished_at=datetime.utcnow().isoformat(),
            )
            return

        _update_ingest_state(progress=95, message="Validatie query…")
        try:
            from sogyo_chatbot.ingestion.vector_store import query_collection

            _ = query_collection("Sogyo traineeship", n_results=1)
        except Exception:
            pass

        if _check_stop():
            return

        _update_ingest_state(
            status="completed",
            progress=100,
            message=(
                f"Klaar! {total_pages} pagina's gescraped, "
                f"{total_inserted} chunks geïndexeerd."
            ),
            finished_at=datetime.utcnow().isoformat(),
            current_source=None,
            pages_scraped=total_pages,
            chunks_indexed=total_inserted,
        )

    except Exception as exc:
        _update_ingest_state(
            status="error",
            message=f"Fout tijdens indexering: {str(exc)}",
            error=str(exc),
            finished_at=datetime.utcnow().isoformat(),
        )
        raise


@app.post("/ingest/start")
async def start_ingest(req: IngestStartRequest, background_tasks: BackgroundTasks):
    """Start indexering (token verplicht — ook bij directe API-aanroep)."""
    global _ingest_state

    if not _check_ingest_token(req.token):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Ongeldig of ontbrekend indexeringstoken.",
            },
        )

    if _ingest_state.get("status") == "running":
        return {"status": "error", "message": "Er loopt al een indexering."}

    _update_ingest_state(
        status="running",
        progress=1,
        message="Voorbereiden… (token OK)",
        stop_requested=False,
        finished_at=None,
        error=None,
        pages_scraped=0,
        chunks_indexed=0,
        started_at=datetime.utcnow().isoformat(),
        current_source=None,
    )

    background_tasks.add_task(_run_ingestion_task, req.max_pages, req.reset)
    return {
        "status": "started",
        "message": "Indexering gestart in de achtergrond.",
        "max_pages": req.max_pages,
        "reset": req.reset,
    }


@app.post("/ingest/stop")
async def stop_ingest(req: IngestStopRequest):
    """Stop lopende indexering (zelfde token als start)."""
    if not _check_ingest_token(req.token):
        return JSONResponse(
            status_code=401,
            content={
                "status": "error",
                "message": "Ongeldig of ontbrekend indexeringstoken.",
            },
        )

    if _ingest_state.get("status") != "running":
        return {"status": "error", "message": "Geen actieve indexering om te stoppen."}

    _ingest_state["stop_requested"] = True
    _ingest_state["message"] = "Stoppen aangevraagd, even geduld…"
    return {"status": "stop_requested", "message": "Stoppen aangevraagd."}


@app.get("/ingest/status")
async def ingest_status():
    """Huidige status van de laatste/geactiveerde indexering."""
    return _ingest_state.copy()


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
