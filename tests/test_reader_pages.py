"""Archive pages must not become the title bronpassing shows."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "reader_pages",
    Path(__file__).resolve().parents[1] / "src/jarvisje/ingestion/reader_pages.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
indexable_page = _mod.indexable_page
present_title = _mod.present_title


def test_wordpress_archives_and_attachments_are_not_articles():
    assert indexable_page("https://edwinvandillen.nl/page/10") is False
    assert indexable_page("https://edwinvandillen.nl/blog/page/24/?paged=3") is False
    assert indexable_page("https://edwinvandillen.nl/?attachment_id=349") is False
    assert indexable_page("https://edwinvandillen.nl/?paged=2&cat=6") is False


def test_real_posts_stay_indexable():
    assert indexable_page("https://edwinvandillen.nl/?p=597") is True
    assert indexable_page("https://edwinvandillen.nl") is True
    assert indexable_page("https://jeroenteunisse.nl/glossarium-de-denkwereld-van-de-blogs") is True


def test_site_banner_is_replaced_by_the_article_heading():
    title = present_title(
        "Edwin van Dillen over Software Innovaties - Part 3",
        "Edwin van Dillen over Software Innovaties - Part 3 > De anatomie van agents — deel 1",
    )
    assert title == "De anatomie van agents — deel 1"


def test_wordpress_tagline_suffix_is_removed():
    title = present_title(
        "Een chatbot die in je eigen content blijft | ... over software engineering ..."
    )
    assert title == "Een chatbot die in je eigen content blijft"
