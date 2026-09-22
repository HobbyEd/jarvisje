"""Heading-aware chunker.

A page is split on markdown headings. A section stays one chunk until its
body exceeds the ceiling; only then it splits on paragraphs, with overlap
inside that section. The heading path is stored as `section` and prefixed
to the text that gets embedded.
"""
from __future__ import annotations

import re
from typing import List

from ..config import settings

Document = dict

_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.MULTILINE)
_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]+\)")


def _clean(text: str) -> str:
    text = _IMAGE.sub("", text or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _sections(text: str) -> List[tuple[List[str], str]]:
    """Return (heading path, body) pairs. Preamble before the first heading has an empty path."""
    matches = list(_HEADING.finditer(text))
    if not matches:
        body = text.strip()
        return [([], body)] if body else []

    sections: List[tuple[List[str], str]] = []
    preamble = text[: matches[0].start()].strip()
    if preamble:
        sections.append(([], preamble))

    stack: List[tuple[int, str]] = []
    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2).strip()
        stack = [(lv, name) for lv, name in stack if lv < level]
        stack.append((level, title))
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        if body:
            sections.append(([name for _, name in stack], body))
    return sections


def _window(text: str, size: int, overlap: int) -> List[str]:
    """Character window for a single paragraph longer than the ceiling."""
    if len(text) <= size:
        return [text] if text else []
    ov = min(overlap, max(0, size - 1))
    chunks: List[str] = []
    start = 0
    while start < len(text):
        piece = text[start : start + size].strip()
        if piece:
            chunks.append(piece)
        if start + size >= len(text):
            break
        start += size - ov
    return chunks


def _pack(body: str, size: int, overlap: int) -> List[str]:
    if len(body) <= size:
        return [body]
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", body) if p.strip()]
    if len(paragraphs) <= 1:
        return _window(body, size, overlap)

    chunks: List[str] = []
    current = ""
    for paragraph in paragraphs:
        if len(paragraph) > size:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_window(paragraph, size, overlap))
            continue
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= size:
            current = candidate
            continue
        if current:
            chunks.append(current)
        tail = ""
        if overlap and current:
            last = current.split("\n\n")[-1].strip()
            tail = last if len(last) <= max(overlap, 400) else current[-overlap:].strip()
        current = f"{tail}\n\n{paragraph}" if tail else paragraph
    if current:
        chunks.append(current.strip())
    return [c for c in chunks if c.strip()]


def _heading_path(title: str, path: List[str]) -> str:
    names = list(path)
    if title and (not names or names[0] != title):
        names = [title, *names]
    return " > ".join(names)


def chunk_document(doc: Document, chunk_size: int | None = None, overlap: int | None = None) -> List[Document]:
    """Split one scraped document into section chunks."""
    text = _clean(str(doc.get("text") or ""))
    if not text:
        return []

    size = chunk_size or settings.chunk_size
    ov = overlap if overlap is not None else settings.chunk_overlap
    title = str(doc.get("title") or "").strip()

    pieces: List[tuple[str, str]] = []
    for path, body in _sections(text):
        section = _heading_path(title, path)
        for part in _pack(body, size, ov):
            shown = f"{section}\n\n{part}" if section else part
            pieces.append((section, shown))

    chunked: List[Document] = []
    total = len(pieces)
    for i, (section, shown) in enumerate(pieces):
        chunked.append(
            {
                **doc,
                "text": shown,
                "section": section,
                "chunk_id": i,
                "chunk_count": total,
            }
        )
    return chunked


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> List[str]:
    """Chunk a bare string. Kept for callers that have no document metadata."""
    docs = chunk_document({"text": text, "title": ""}, chunk_size=chunk_size, overlap=overlap)
    return [d["text"] for d in docs]


def chunk_documents(docs: List[Document]) -> List[Document]:
    """Chunk a list of documents."""
    result: List[Document] = []
    for doc in docs:
        result.extend(chunk_document(doc))
    return result
