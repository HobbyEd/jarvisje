"""Which crawled URLs are articles, and how their title should be shown.

edwinvandillen.nl also stores WordPress archives (/page/N, ?paged=) and
attachments. Their title is the site banner, so bronpassing would name
"Edwin van Dillen over Software Innovaties - Part 3" instead of the article.
"""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

_SITE_SUFFIX = re.compile(
    r"\s*\|\s*\.\.\.\s*over software engineering\s*\.\.\.\s*$",
    re.IGNORECASE,
)
_ARCHIVE_TITLE = re.compile(
    r"^edwin van dillen over software innovaties(?:\s*-\s*part\s+\d+)?$",
    re.IGNORECASE,
)
_FILE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".pdf", ".zip", ".xml")
_BANNER = {"blog", "image", "contact"}


def indexable_page(url: str) -> bool:
    """True for a page a reader would open as an article or the site home."""
    raw = (url or "").strip()
    if not raw:
        return False
    parsed = urlparse(raw)
    path = (parsed.path or "").lower()
    if path.rstrip("/").endswith(_FILE_SUFFIXES):
        return False
    if re.search(r"/page/\d+/?$", path):
        return False
    if any(part in path for part in ("/tag/", "/category/", "/author/", "/feed", "/wp-json", "/attachment/")):
        return False
    query = {key.lower(): value for key, value in parse_qs(parsed.query).items()}
    if "attachment_id" in query or "paged" in query or "cat" in query or "tag" in query:
        return False
    return True


def present_title(title: str, section: str = "") -> str:
    """Article name without the site banner or the WordPress tagline suffix."""
    cleaned = _strip(title)
    if cleaned and not _is_banner(cleaned):
        return cleaned
    for part in reversed(_parts(section)):
        part = _strip(part)
        if part and not _is_banner(part):
            return part
    return cleaned or "Bron"


def _strip(value: str) -> str:
    return _SITE_SUFFIX.sub("", (value or "").strip()).strip(" |-")


def _parts(section: str) -> list[str]:
    return [part.strip() for part in (section or "").split(">") if part.strip()]


def _is_banner(value: str) -> bool:
    text = value.strip()
    if not text:
        return True
    if text.casefold() in _BANNER:
        return True
    return _ARCHIVE_TITLE.match(text) is not None
