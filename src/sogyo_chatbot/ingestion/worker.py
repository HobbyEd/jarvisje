"""
Standalone ingestion worker (ADR-010).

Same entrypoint for UI-spawn, CLI, and future cron:

    python -m sogyo_chatbot.ingestion.worker
    python -m sogyo_chatbot.ingestion.worker --max-pages 500 --reset
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
import time
import traceback

from sogyo_chatbot.config import settings
from sogyo_chatbot.ingestion import chunk_documents, embed_chunks, upsert_chunks
from sogyo_chatbot.ingestion.scraper import scrape_domain
from sogyo_chatbot.ingestion.status import (
    clear_stop_flag,
    new_run_id,
    release_lock,
    stop_requested,
    try_acquire_lock,
    utc_now_iso,
    write_status,
)
from sogyo_chatbot.ingestion.vector_store import (
    _get_collection_name,
    get_chroma_client,
    get_chroma_store,
    get_indexed_page_index,
    query_collection,
)


def _update(**kwargs) -> None:
    write_status(kwargs)


def _check_stop() -> bool:
    if stop_requested():
        _update(
            status="stopped",
            message="Indexering gestopt door gebruiker.",
            finished_at=utc_now_iso(),
            current_source=None,
            stop_requested=False,
        )
        clear_stop_flag()
        return True
    return False


def run_ingest(max_pages: int | None = None, reset: bool = False) -> int:
    """Run full multi-source ingest. Returns process exit code."""
    pid = os.getpid()
    run_id = new_run_id()

    if not try_acquire_lock(pid):
        print("Another ingest worker holds the lock.", file=sys.stderr)
        # Do not touch status — the holding worker owns it.
        return 2

    # Honour stop requested during API→worker handoff (API clears flag only on *start*).
    if stop_requested():
        release_lock(pid)
        _update(
            status="stopped",
            message="Indexering gestopt voordat de worker begon.",
            finished_at=utc_now_iso(),
            current_source=None,
            stop_requested=False,
            pid=None,
        )
        clear_stop_flag()
        return 0

    try:
        # Own the status file only after the lock is ours.
        _update(
            status="running",
            progress=5,
            message="Indexering gestart (aparte worker)…",
            started_at=utc_now_iso(),
            finished_at=None,
            current_source=None,
            error=None,
            stop_requested=False,
            pages_scraped=0,
            chunks_indexed=0,
            pid=pid,
            run_id=run_id,
        )

        coll_name = _get_collection_name()
        incremental = not reset
        known_pages: dict = {}

        if reset:
            _update(progress=8, message="Bestaande index wissen (volledige herindexering)…")
            client = get_chroma_client()
            try:
                client.delete_collection(coll_name)
            except Exception:
                pass
            import sogyo_chatbot.ingestion.vector_store as vs

            vs._collection = None
            get_chroma_store()
            time.sleep(0.2)
        else:
            _update(
                progress=6,
                message="Bestaande index laden (alleen nieuw/gewijzigd)…",
                incremental=True,
            )
            try:
                known_pages = get_indexed_page_index()
            except Exception as exc:
                print(f"Could not load index for incremental skip: {exc}", file=sys.stderr)
                known_pages = {}
            _update(
                message=(
                    f"Incrementeel: {len(known_pages)} bekende URL's — "
                    "sitemap check op nieuw/gewijzigd…"
                ),
                pages_skipped=0,
            )

        if _check_stop():
            return 0

        sources = settings.sources
        total_inserted = 0
        total_pages = 0
        total_skipped = 0
        batch_size = settings.ingest_batch_size
        n_sources = max(1, len(sources))
        crawl_stats: dict[str, int] = {"skipped": 0, "extracted": 0}

        def index_batch(domain: str, docs: list) -> None:
            nonlocal total_inserted, total_pages
            if not docs:
                return
            total_pages += len(docs)
            _update(
                message=f"Indexeren batch {domain} ({len(docs)} pagina's)…",
                current_source=domain,
                pages_scraped=total_pages,
                pages_skipped=total_skipped,
            )
            chunked = chunk_documents(docs)
            if not chunked:
                return
            texts = [c["text"] for c in chunked]
            embeddings = embed_chunks(texts)
            upsert_bs = 64
            for b in range(0, len(chunked), upsert_bs):
                if stop_requested():
                    return
                n = upsert_chunks(
                    chunked[b : b + upsert_bs], embeddings[b : b + upsert_bs]
                )
                total_inserted += n
                _update(chunks_indexed=total_inserted)
                time.sleep(0.1)
            gc.collect()

        for idx, start_url in enumerate(sources):
            domain = start_url.replace("https://", "").replace("http://", "").rstrip("/")
            base_pct = 10 + int((idx / n_sources) * 80)
            pages_before = total_pages
            mode_label = "incrementeel" if incremental else "volledig"

            def progress_cb(
                d_domain: str,
                scraped_count: int,
                current_url: str | None = None,
                *,
                _domain=domain,
                _base=base_pct,
                _before=pages_before,
            ) -> None:
                slice_w = max(5, 80 // n_sources)
                within = min(
                    slice_w - 1,
                    int((scraped_count / max(50, scraped_count + 10)) * slice_w),
                )
                live = min(92, _base + within)
                cur = _domain
                if current_url:
                    cur = f"{_domain} — {current_url[:80]}"
                _update(
                    progress=live,
                    message=f"Scrapen {_domain} ({mode_label})… ({scraped_count} nieuw)",
                    current_source=cur,
                    pages_scraped=_before + scraped_count,
                    pages_skipped=total_skipped + crawl_stats.get("skipped", 0),
                )

            def batch_cb(docs: list, *, _domain=domain) -> None:
                if stop_requested():
                    return
                index_batch(_domain, docs)

            _update(
                progress=base_pct,
                message=f"Bron {idx + 1}/{n_sources}: {domain} ({mode_label})",
                current_source=domain,
                incremental=incremental,
            )
            if _check_stop():
                return 0

            scrape_domain(
                start_url,
                max_pages=max_pages,
                progress_callback=progress_cb,
                batch_callback=batch_cb,
                batch_size=batch_size,
                known_pages=known_pages if incremental else None,
                incremental=incremental,
                stats_out=crawl_stats,
            )
            total_skipped = crawl_stats.get("skipped", 0)
            _update(pages_skipped=total_skipped)
            if _check_stop():
                return 0
            time.sleep(0.3)
            gc.collect()

        if total_pages == 0 and total_inserted == 0:
            msg = (
                f"Geen nieuwe of gewijzigde pagina's "
                f"({total_skipped} al geïndexeerd overgeslagen)."
                if incremental and total_skipped
                else "Geen documenten gevonden."
            )
            _update(
                status="completed",
                progress=100,
                message=msg,
                finished_at=utc_now_iso(),
                current_source=None,
                pages_skipped=total_skipped,
                incremental=incremental,
            )
            return 0

        _update(progress=95, message="Validatie query…")
        try:
            query_collection("Sogyo traineeship", n_results=1)
        except Exception:
            pass

        if _check_stop():
            return 0

        if incremental:
            done_msg = (
                f"Klaar (incrementeel)! {total_pages} pagina's bijgewerkt, "
                f"{total_inserted} chunks, {total_skipped} overgeslagen."
            )
        else:
            done_msg = (
                f"Klaar (volledige herindexering)! {total_pages} pagina's gescraped, "
                f"{total_inserted} chunks geïndexeerd."
            )
        _update(
            status="completed",
            progress=100,
            message=done_msg,
            finished_at=utc_now_iso(),
            current_source=None,
            pages_scraped=total_pages,
            pages_skipped=total_skipped,
            chunks_indexed=total_inserted,
            stop_requested=False,
            incremental=incremental,
        )
        clear_stop_flag()
        print(
            f"Ingestion complete: pages={total_pages} chunks={total_inserted} "
            f"skipped={total_skipped} incremental={incremental} run_id={run_id}"
        )
        return 0

    except Exception as exc:
        tb = traceback.format_exc()
        print(tb, file=sys.stderr)
        _update(
            status="error",
            message=f"Fout tijdens indexering: {exc}",
            error=str(exc),
            finished_at=utc_now_iso(),
            current_source=None,
        )
        return 1
    finally:
        release_lock(pid)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sogyo async ingestion worker (ADR-010)")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Max content pages per domain (0 = hard cap)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe Chroma collection before ingest",
    )
    args = parser.parse_args(argv)

    print("=== Sogyo ingestion worker ===")
    print(f"data_dir     : {settings.data_dir}")
    print(f"chroma       : {settings.chroma_persist_dir}")
    print(f"embedding    : {settings.embedding_model}")
    print(f"max_pages    : {args.max_pages}")
    print(f"reset        : {args.reset}")
    print(f"pid          : {os.getpid()}")
    return run_ingest(max_pages=args.max_pages, reset=args.reset)


if __name__ == "__main__":
    sys.exit(main())
