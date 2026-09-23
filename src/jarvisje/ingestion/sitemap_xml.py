"""Sitemap element lookup.

ElementTree treats an element that only contains text as false. A test like
`parent.find("s:loc") or parent.find("loc")` therefore drops every
`<loc>https://…</loc>`, including All in One SEO CDATA locs.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET


def xml_find(parent: ET.Element, namespaced: str, plain: str, ns: dict) -> ET.Element | None:
    found = parent.find(namespaced, ns)
    if found is None:
        found = parent.find(plain)
    return found


def xml_text(element: ET.Element | None) -> str | None:
    if element is None or element.text is None:
        return None
    value = element.text.strip()
    return value or None
