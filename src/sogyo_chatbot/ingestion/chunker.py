"""
Simple chunker for the MVP.

Character-based with overlap. Sufficient for first version.
Can be upgraded later to heading-aware or token-aware chunking.
"""
from __future__ import annotations

from typing import List

from ..config import settings

Document = dict


def chunk_text(text: str, chunk_size: int | None = None, overlap: int | None = None) -> List[str]:
    """
    Split text into overlapping chunks.
    """
    size = chunk_size or settings.chunk_size
    ov = overlap or settings.chunk_overlap

    if len(text) <= size:
        return [text]

    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = start + size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += size - ov

    return chunks


def chunk_document(doc: Document) -> List[Document]:
    """
    Take a scraped document and return list of chunk documents with metadata.
    """
    text = doc.get("text", "")
    if not text:
        return []

    raw_chunks = chunk_text(text)

    chunked_docs: List[Document] = []
    for i, chunk in enumerate(raw_chunks):
        chunk_doc = {
            **doc,
            "text": chunk,
            "chunk_id": i,
            "chunk_count": len(raw_chunks),
        }
        chunked_docs.append(chunk_doc)

    return chunked_docs


def chunk_documents(docs: List[Document]) -> List[Document]:
    """Chunk a list of documents."""
    result = []
    for d in docs:
        result.extend(chunk_document(d))
    return result
