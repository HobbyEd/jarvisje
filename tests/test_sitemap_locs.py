"""CDATA sitemap locs must survive ElementTree's falsy elements."""
import importlib.util
import xml.etree.ElementTree as ET
from pathlib import Path

NS = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<sitemap><loc><![CDATA[https://edwinvandillen.nl/post-sitemap.xml]]></loc></sitemap>
</sitemapindex>
"""
URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url>
<loc><![CDATA[https://edwinvandillen.nl/?p=597]]></loc>
<lastmod><![CDATA[2026-09-23T16:55:16+00:00]]></lastmod>
</url>
</urlset>
"""


def _load():
    path = Path(__file__).resolve().parents[1] / "src" / "jarvisje" / "ingestion" / "sitemap_xml.py"
    spec = importlib.util.spec_from_file_location("sitemap_xml", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


xml = _load()


def test_index_loc_is_not_dropped():
    root = ET.fromstring(INDEX)
    sm = root.findall(".//s:sitemap", NS)[0]
    assert xml.xml_text(xml.xml_find(sm, "s:loc", "loc", NS)) == (
        "https://edwinvandillen.nl/post-sitemap.xml"
    )


def test_post_loc_and_lastmod():
    root = ET.fromstring(URLSET)
    url = root.findall(".//s:url", NS)[0]
    assert xml.xml_text(xml.xml_find(url, "s:loc", "loc", NS)) == "https://edwinvandillen.nl/?p=597"
    assert xml.xml_text(xml.xml_find(url, "s:lastmod", "lastmod", NS)) == "2026-09-23T16:55:16+00:00"


if __name__ == "__main__":
    test_index_loc_is_not_dropped()
    test_post_loc_and_lastmod()
    print("ok")
