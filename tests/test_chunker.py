"""Heading blocks stay intact; overlap does not cross a heading."""
import importlib.util
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"


def _load_chunker():
    if str(SRC) not in sys.path:
        sys.path.insert(0, str(SRC))
    import jarvisje  # noqa: F401
    pkg = types.ModuleType("jarvisje.ingestion")
    pkg.__path__ = [str(SRC / "jarvisje" / "ingestion")]
    pkg.__package__ = "jarvisje.ingestion"
    sys.modules["jarvisje.ingestion"] = pkg
    spec = importlib.util.spec_from_file_location(
        "jarvisje.ingestion.chunker",
        SRC / "jarvisje" / "ingestion" / "chunker.py",
    )
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "jarvisje.ingestion"
    sys.modules["jarvisje.ingestion.chunker"] = module
    spec.loader.exec_module(module)
    return module


chunker = _load_chunker()


def test_headings_do_not_bleed():
    text = "# Titel\n\nInleiding van het stuk.\n\n## De stelling\n\nDe stelling zelf.\n\n## Gevolgen\n\nWat eruit volgt."
    docs = chunker.chunk_document({"title": "Titel", "text": text, "url": "https://edwinvandillen.nl/x"})
    assert len(docs) == 3
    assert docs[0]["section"] == "Titel"
    assert docs[1]["section"] == "Titel > De stelling"
    assert "Gevolgen" not in docs[1]["text"]
    assert "De stelling zelf" not in docs[2]["text"]
    assert docs[2]["text"].startswith("Titel > Gevolgen")


def test_short_page_is_one_chunk():
    docs = chunker.chunk_document({"title": "Kort", "text": "Alleen een alinea zonder kopje."})
    assert len(docs) == 1
    assert docs[0]["section"] == "Kort"
    assert "Alleen een alinea" in docs[0]["text"]


def test_long_section_splits_on_paragraphs_inside_the_heading():
    body = "\n\n".join(f"Alinea {i} " + ("woord " * 80) for i in range(6))
    text = f"## Lang\n\n{body}"
    docs = chunker.chunk_document(
        {"title": "Artikel", "text": text},
        chunk_size=500,
        overlap=40,
    )
    assert len(docs) >= 2
    assert all(d["section"] == "Artikel > Lang" for d in docs)
    assert docs[0]["chunk_count"] == len(docs)


if __name__ == "__main__":
    test_headings_do_not_bleed()
    test_short_page_is_one_chunk()
    test_long_section_splits_on_paragraphs_inside_the_heading()
    print("ok")
