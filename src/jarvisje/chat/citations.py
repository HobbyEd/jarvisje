"""Align in-text [n] markers with the citation list the reader sees.

The prompt numbers retrieved fragments [1]..[6]. The model cites those slot
numbers. After the allowlist filter the shown list is shorter, so a visible
[5] would not match the third link. This rewrites the markers to the list
that is actually returned.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urlparse

from ..config import settings
from .models import Citation

_SLOT = re.compile(r"\[(\d+)\]")
_FILE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf")


def _norm_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    host = parsed.netloc.lower().lstrip("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}".lower()


def _allowed(url: str) -> bool:
    low = (url or "").lower().split("?", 1)[0]
    if low.endswith(_FILE_SUFFIXES):
        return False
    return settings.is_allowed_url(url)


def _slots(retrieved: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    slots: List[Dict[str, str]] = []
    for i, hit in enumerate(retrieved[:6], 1):
        meta = hit.get("metadata") or {}
        url = str(meta.get("url") or "")
        title = str(meta.get("title") or url or "Bron")
        source = str(meta.get("source") or "")
        slots.append({"n": str(i), "url": url, "title": title, "source": source})
    return slots


def _citation(slot: Dict[str, str]) -> Citation:
    return Citation(
        title=slot["title"],
        url=slot["url"],
        source=slot["source"] or None,
    )


def _tidy(answer: str) -> str:
    text = re.sub(r"\(\s*\)", "", answer)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" +([.,;:])", r"\1", text)
    return text.strip()


def align_answer_citations(
    answer: str,
    citations: List[Citation],
    retrieved: List[Dict[str, Any]],
) -> tuple[str, List[Citation]]:
    """Return answer text and citations whose numbers match.

    [n] in the answer refers to retrieval slot n. Kept slots are renumbered
    in order of first appearance. Model citations that name a retrieved URL
    but were not marked are appended after those.
    """
    slots = [s for s in _slots(retrieved) if _allowed(s["url"])]
    by_n = {int(s["n"]): s for s in slots}
    by_url: Dict[str, Dict[str, str]] = {}
    for slot in slots:
        by_url.setdefault(_norm_url(slot["url"]), slot)

    marks = [int(m.group(1)) for m in _SLOT.finditer(answer or "")]
    ordered: List[Dict[str, str]] = []
    seen: set[str] = set()

    if marks:
        for n in marks:
            slot = by_n.get(n)
            if not slot:
                continue
            key = _norm_url(slot["url"])
            if key in seen:
                continue
            seen.add(key)
            ordered.append(slot)

        url_to_new = {_norm_url(s["url"]): i for i, s in enumerate(ordered, 1)}
        slot_to_new = {
            int(s["n"]): url_to_new[_norm_url(s["url"])]
            for s in slots
            if _norm_url(s["url"]) in url_to_new
        }

        def repl(match: re.Match[str]) -> str:
            new = slot_to_new.get(int(match.group(1)))
            return f"[{new}]" if new else ""

        answer = _tidy(_SLOT.sub(repl, answer or ""))

        for cite in citations:
            key = _norm_url(cite.url)
            slot = by_url.get(key)
            if not slot or key in seen:
                continue
            seen.add(key)
            ordered.append(slot)
        return answer, [_citation(s) for s in ordered]

    kept: List[Citation] = []
    for cite in citations:
        key = _norm_url(cite.url)
        slot = by_url.get(key)
        if not slot or key in seen:
            continue
        seen.add(key)
        kept.append(_citation(slot))
    return answer, kept
