"""
Polite web scraper for the Sogyo-related domains.

Strategy (2026-08):
1. Discover all page URLs from sitemaps (recursive) + lastmod when available
2. Prioritize article-like URLs (blog/posts/dates) over pagination/taxonomy
3. Process sitemap URLs first so re-index reaches all posts (e.g. 63+ blogs)
4. Optional BFS expansion for remaining budget
5. Support batch callbacks for progressive embed/upsert
"""
from __future__ import annotations

import json
import re
import time
import warnings
import xml.etree.ElementTree as ET
from collections import deque
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
import trafilatura
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from tqdm import tqdm

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from ..config import settings

Document = Dict[str, str | int]

# progress_callback(domain, scraped_count, current_url)
ProgressCallback = Callable[[str, int, Optional[str]], None]
# batch_callback(docs) — process a batch while crawl continues
BatchCallback = Callable[[List[Document]], None]


def _get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def _is_same_domain(base: str, candidate: str) -> bool:
    b = _get_domain(base).lstrip("www.")
    c = _get_domain(candidate).lstrip("www.")
    return b == c


def _clean_url(url: str) -> str:
    """Remove fragments; normalize http→https; strip trailing slash."""
    parsed = urlparse(url)
    if parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")
    clean = parsed._replace(fragment="").geturl()
    return clean.rstrip("/")


def _article_score(url: str) -> int:
    """Higher = more likely a real article/post (process first)."""
    u = url.lower()
    score = 0
    if re.search(r"/20\d{2}/\d{1,2}/", u):
        score += 20
    if re.search(r"/20\d{2}/", u):
        score += 12
    if any(x in u for x in ("/blog", "/post", "/posts", "/artikel", "/nieuws", "/article")):
        score += 10
    depth = u.rstrip("/").count("/")
    if depth >= 4:
        score += 4
    elif depth >= 3:
        score += 2
    # Taxonomy / pagination / noise
    if re.search(r"/page/\d+", u) or re.search(r"[?&]page=\d+", u):
        score -= 15
    if any(x in u for x in ("/tag/", "/category/", "/author/", "/wp-json", "/feed", "/cart", "/login")):
        score -= 12
    if u.rstrip("/").endswith((".xml", ".jpg", ".png", ".pdf", ".zip")):
        score -= 50
    return score


def _fetch_text(client: httpx.Client, url: str) -> Optional[str]:
    for attempt in range(2):
        try:
            resp = client.get(url, timeout=settings.request_timeout, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            if resp.status_code in (403, 429) and attempt == 0:
                headers = dict(client.headers)
                headers["User-Agent"] = (
                    "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
                )
                resp2 = client.get(
                    url, timeout=settings.request_timeout, headers=headers, follow_redirects=True
                )
                if resp2.status_code == 200:
                    return resp2.text
        except Exception:
            if attempt == 1:
                pass
    return None


def _get_robots_parser(domain_url: str, client: httpx.Client) -> RobotFileParser:
    rp = RobotFileParser()
    robots_url = urljoin(domain_url, "/robots.txt")
    robots_text = _fetch_text(client, robots_url) or ""
    rp.parse(robots_text.splitlines())
    return rp


def _get_sitemaps_from_robots(domain_url: str, client: httpx.Client) -> list[str]:
    robots_url = urljoin(domain_url, "/robots.txt")
    text = _fetch_text(client, robots_url) or ""
    sitemaps = []
    for line in text.splitlines():
        if line.lower().strip().startswith("sitemap:"):
            sm = line.split(":", 1)[1].strip()
            if sm.startswith("http"):
                sitemaps.append(sm)
    return sitemaps


def _collect_pages_from_sitemaps(
    domain_url: str, client: httpx.Client
) -> List[Tuple[str, Optional[str]]]:
    """Return list of (page_url, lastmod_iso_or_None) from sitemaps."""
    candidates = [
        urljoin(domain_url, "/sitemap.xml"),
        urljoin(domain_url, "/sitemap_index.xml"),
        urljoin(domain_url, "/wp-sitemap.xml"),
        urljoin(domain_url, "/wp-sitemap-posts-post-1.xml"),
        urljoin(domain_url, "/sitemaps/sitemap.xml"),
    ]
    for sm in _get_sitemaps_from_robots(domain_url, client):
        if sm not in candidates:
            candidates.append(sm)

    to_process: List[str] = list(candidates)
    processed: Set[str] = set()
    # url -> lastmod
    page_map: Dict[str, Optional[str]] = {}
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    while to_process:
        sm_url = to_process.pop(0)
        if sm_url in processed:
            continue
        processed.add(sm_url)

        text = _fetch_text(client, sm_url)
        if not text:
            continue
        try:
            root = ET.fromstring(text)
            sitemaps = root.findall(".//s:sitemap", ns) + root.findall(".//sitemap")
            if sitemaps:
                for sm in sitemaps:
                    loc_el = sm.find("s:loc", ns) or sm.find("loc")
                    if loc_el is not None and loc_el.text:
                        loc = _clean_url(loc_el.text.strip())
                        if loc.startswith("http") and loc not in processed:
                            to_process.append(loc)
            else:
                urls = root.findall(".//s:url", ns) + root.findall(".//url")
                for u in urls:
                    loc_el = u.find("s:loc", ns) or u.find("loc")
                    if loc_el is None or not loc_el.text:
                        continue
                    loc = _clean_url(loc_el.text.strip())
                    if not loc.startswith("http") or loc.endswith(".xml"):
                        continue
                    lastmod_el = u.find("s:lastmod", ns) or u.find("lastmod")
                    lastmod = None
                    if lastmod_el is not None and lastmod_el.text:
                        lastmod = lastmod_el.text.strip()
                    # Keep newest lastmod if duplicate
                    prev = page_map.get(loc)
                    if prev is None or (lastmod and lastmod > (prev or "")):
                        page_map[loc] = lastmod
        except ET.ParseError:
            continue
        except Exception:
            continue

    items = list(page_map.items())
    items.sort(key=lambda t: (_article_score(t[0]), t[1] or ""), reverse=True)
    return items


def _extract_page(url: str, html: str, lastmod: Optional[str] = None) -> Optional[Document]:
    """Use trafilatura for clean main-content extraction."""
    try:
        extracted = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            include_links=False,
            favor_recall=True,
        )
        metadata = trafilatura.extract_metadata(html)
        title = (getattr(metadata, "title", None) if metadata else None) or url
        published = None
        if metadata is not None:
            published = getattr(metadata, "date", None) or getattr(metadata, "published", None)
            if published is not None:
                published = str(published)

        domain = _get_domain(url)
        ingested_at = datetime.now(timezone.utc).isoformat()
        article_date = published or lastmod

        if not extracted or len(extracted.strip()) < 120:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
                    soup = BeautifulSoup(html, "lxml")
                text = soup.get_text(separator=" ", strip=True)
                if len(text) > 50:
                    title_s = (
                        soup.title.string.strip()
                        if soup.title and soup.title.string
                        else str(title).strip()
                    )
                    return {
                        "url": url,
                        "title": title_s,
                        "text": text[:10000],
                        "source": domain,
                        "length": len(text),
                        "ingested_at": ingested_at,
                        "article_date": article_date or "",
                        "lastmod": lastmod or "",
                    }
            except Exception:
                pass
            return None

        return {
            "url": url,
            "title": str(title).strip(),
            "text": extracted.strip(),
            "source": domain,
            "length": len(extracted),
            "ingested_at": ingested_at,
            "article_date": article_date or "",
            "lastmod": lastmod or "",
        }
    except Exception:
        return None


def _resolve_page_limit(max_pages: int | None) -> int:
    """Normalize max_pages: None → setting; 0/neg → hard cap."""
    hard = max(1, settings.hard_cap_pages_per_domain)
    if max_pages is None:
        return min(max(1, settings.max_pages_per_domain), hard)
    if max_pages <= 0:
        return hard
    return min(max_pages, hard)


def _needs_refetch(
    url: str,
    *,
    known: Dict[str, Dict[str, str]],
    lastmod_map: Dict[str, Optional[str]],
) -> bool:
    """True if URL is unknown or sitemap lastmod is newer than stored."""
    if url not in known:
        return True
    sitemap_lm = (lastmod_map.get(url) or "").strip()
    stored_lm = (known[url].get("lastmod") or "").strip()
    if sitemap_lm and stored_lm and sitemap_lm > stored_lm:
        return True
    if sitemap_lm and not stored_lm:
        # Have a sitemap signal but never stored a date — treat as refresh candidate
        return True
    return False


def scrape_domain(
    start_url: str,
    max_pages: int | None = None,
    save_raw: bool = True,
    progress_callback: Optional[ProgressCallback] = None,
    batch_callback: Optional[BatchCallback] = None,
    batch_size: int | None = None,
    known_pages: Optional[Dict[str, Dict[str, str]]] = None,
    incremental: bool = False,
    stats_out: Optional[Dict[str, int]] = None,
) -> List[Document]:
    """
    Crawl a single domain: sitemap-first (article priority), then light BFS.

    - max_pages limits extracted *content* pages (not raw visits of empty shells).
    - batch_callback receives batches of documents for progressive indexing.
    - incremental + known_pages: skip URLs already in the index unless sitemap
      lastmod is newer (reset=False path). Full crawl when incremental=False.
    - stats_out: optional dict filled with skipped/extracted counts.
    """
    limit = _resolve_page_limit(max_pages)
    bsize = batch_size or settings.ingest_batch_size
    domain = _get_domain(start_url)
    known = known_pages or {}

    visited: Set[str] = set()
    documents: List[Document] = []
    pending_batch: List[Document] = []
    skipped = 0
    # url -> lastmod from sitemap
    lastmod_map: Dict[str, Optional[str]] = {}

    headers = {"User-Agent": settings.user_agent}
    client = httpx.Client(headers=headers, follow_redirects=True, timeout=settings.request_timeout)
    rp = _get_robots_parser(start_url, client)

    sitemap_items = _collect_pages_from_sitemaps(start_url, client)
    for u, lm in sitemap_items:
        if _is_same_domain(start_url, u):
            lastmod_map[_clean_url(u)] = lm

    # Queue: article-priority sitemap URLs first, then home, then pagination seeds
    sitemap_urls = [
        _clean_url(u) for u, _ in sitemap_items if _is_same_domain(start_url, u)
    ]
    to_visit: deque[str] = deque()
    seen_q: Set[str] = set()

    def _enqueue(u: str, front: bool = False) -> None:
        cu = _clean_url(u)
        if cu in seen_q or cu in visited:
            return
        # Incremental: never queue pages we will skip (keeps crawl short)
        if incremental and known and not _needs_refetch(
            cu, known=known, lastmod_map=lastmod_map
        ):
            return
        seen_q.add(cu)
        if front:
            to_visit.appendleft(cu)
        else:
            to_visit.append(cu)

    if incremental and known:
        new_urls: List[str] = []
        refresh_urls: List[str] = []
        for u in sitemap_urls:
            if u not in known:
                new_urls.append(u)
            elif _needs_refetch(u, known=known, lastmod_map=lastmod_map):
                refresh_urls.append(u)
            else:
                skipped += 1
        # Newest/most article-like first among new posts
        new_urls.sort(key=_article_score, reverse=True)
        refresh_urls.sort(key=_article_score, reverse=True)
        for u in new_urls:
            _enqueue(u)
        for u in refresh_urls:
            _enqueue(u)
        # Light discovery only if sitemap is thin (unknown non-sitemap pages)
        if len(sitemap_urls) < 20:
            _enqueue(start_url, front=True)
            for i in range(1, 31):
                _enqueue(urljoin(start_url, f"/page/{i}"))
                _enqueue(urljoin(start_url, f"/blog/page/{i}"))
            for suffix in ("/blog", "/posts", "/archive", "/category"):
                _enqueue(urljoin(start_url, suffix))
        print(
            f"[{domain}] Incremental: {len(new_urls)} new, "
            f"{len(refresh_urls)} refresh, {skipped} already indexed (skipped)"
        )
    else:
        for u in sitemap_urls:
            _enqueue(u)
        _enqueue(start_url, front=True)
        # If sitemap thin: seed pagination/archives to discover posts
        if len(sitemap_urls) < 20:
            for i in range(1, 31):
                _enqueue(urljoin(start_url, f"/page/{i}"))
                _enqueue(urljoin(start_url, f"/blog/page/{i}"))
            for suffix in ("/blog", "/posts", "/archive", "/category"):
                _enqueue(urljoin(start_url, suffix))

    def _flush_batch(force: bool = False) -> None:
        nonlocal pending_batch
        if not batch_callback or not pending_batch:
            return
        if not force and len(pending_batch) < bsize:
            return
        try:
            batch_callback(list(pending_batch))
        except Exception as exc:
            print(f"[{domain}] batch_callback error: {exc}")
        pending_batch = []

    def _accept_doc(doc: Document) -> None:
        documents.append(doc)
        pending_batch.append(doc)
        if save_raw:
            safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", str(doc["url"]))[:120]
            raw_path = settings.raw_dir / f"{domain}__{safe_name}.json"
            raw_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        _flush_batch(force=False)

    pbar = tqdm(total=limit, desc=f"Scraping {domain}", unit="page")
    # Allow more visits than docs (nav pages that fail extract still cost budget lightly)
    max_visits = limit * 3

    while to_visit and len(documents) < limit and len(visited) < max_visits:
        url = _clean_url(to_visit.popleft())
        if url in visited:
            continue

        if incremental and known and not _needs_refetch(
            url, known=known, lastmod_map=lastmod_map
        ):
            visited.add(url)
            skipped += 1
            continue

        if not rp.can_fetch(settings.user_agent, url):
            visited.add(url)
            continue

        html = _fetch_text(client, url)
        if not html:
            visited.add(url)
            continue

        visited.add(url)

        doc = _extract_page(url, html, lastmod=lastmod_map.get(url))
        if doc:
            _accept_doc(doc)
            pbar.update(1)
            if progress_callback:
                try:
                    progress_callback(domain, len(documents), url)
                except Exception:
                    pass

        # Discover links (BFS) — only while under limit; sitemap already covered most posts
        if not url.endswith(".xml") and len(documents) < limit:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", XMLParsedAsHTMLWarning)
                    soup = BeautifulSoup(html, "lxml")
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    absolute = urljoin(url, href)
                    clean = _clean_url(absolute)
                    if (
                        _is_same_domain(start_url, clean)
                        and clean not in visited
                        and clean not in seen_q
                        and not any(
                            x in clean
                            for x in (".pdf", ".jpg", ".png", ".zip", "mailto:", "javascript:")
                        )
                    ):
                        # Prefer high-score URLs at front of remaining queue
                        if _article_score(clean) >= 8:
                            _enqueue(clean, front=True)
                        else:
                            _enqueue(clean)
            except Exception:
                pass

        time.sleep(settings.request_delay_seconds)

    _flush_batch(force=True)
    pbar.close()
    client.close()

    print(
        f"[{domain}] Extracted {len(documents)} pages "
        f"(visited {len(visited)}, skipped {skipped}, "
        f"sitemap seeds {len(sitemap_urls)}, limit {limit}, "
        f"incremental={incremental})"
    )
    if stats_out is not None:
        stats_out["skipped"] = int(stats_out.get("skipped", 0)) + skipped
        stats_out["extracted"] = int(stats_out.get("extracted", 0)) + len(documents)
    return documents


def scrape_all_sources(
    max_pages_per_domain: int | None = None,
    progress_callback: Optional[ProgressCallback] = None,
) -> List[Document]:
    """Scrape all configured sources."""
    all_docs: List[Document] = []
    for url in settings.sources:
        docs = scrape_domain(
            url, max_pages=max_pages_per_domain, progress_callback=progress_callback
        )
        all_docs.extend(docs)
    return all_docs
