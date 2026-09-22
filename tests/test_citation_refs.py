"""Slot numbers in the answer must match the citation list."""
from jarvisje.chat.citations import align_answer_citations
from jarvisje.chat.models import Citation


def _hit(n_title: str, url: str):
    return {"text": "fragment", "metadata": {"title": n_title, "url": url, "source": "edwinvandillen.nl"}}


def test_slot_five_renumbers_to_first_shown_source():
    retrieved = [
        _hit("A", "https://edwinvandillen.nl/a"),
        _hit("B", "https://edwinvandillen.nl/b"),
        _hit("C", "https://jeroenteunisse.nl/c"),
        _hit("D", "https://edwinvandillen.nl/d"),
        _hit("E", "https://edwinvandillen.nl/e"),
        _hit("Plaatje", "https://edwinvandillen.nl/plaatje.png"),
    ]
    model_citations = [
        Citation(title="A", url="https://edwinvandillen.nl/a", source="edwinvandillen.nl"),
        Citation(title="E", url="https://edwinvandillen.nl/e", source="edwinvandillen.nl"),
        Citation(title="plaatje", url="https://edwinvandillen.nl/plaatje.png", source="edwinvandillen.nl"),
        Citation(title="vreemd", url="https://example.com/x", source="example.com"),
    ]
    answer, citations = align_answer_citations(
        "Dat staat in [5], niet in het plaatje [6].",
        model_citations,
        retrieved,
    )
    assert answer == "Dat staat in [1], niet in het plaatje."
    assert [c.url for c in citations] == [
        "https://edwinvandillen.nl/e",
        "https://edwinvandillen.nl/a",
    ]


def test_same_article_keeps_one_number():
    retrieved = [
        _hit("Artikel", "https://edwinvandillen.nl/post"),
        _hit("Artikel", "https://edwinvandillen.nl/post/"),
    ]
    answer, citations = align_answer_citations(
        "Zie [1] en ook [2].",
        [],
        retrieved,
    )
    assert answer == "Zie [1] en ook [1]."
    assert len(citations) == 1
    assert citations[0].title == "Artikel"


def test_without_markers_only_retrieved_urls_remain():
    retrieved = [_hit("A", "https://edwinvandillen.nl/a")]
    answer, citations = align_answer_citations(
        "Geen nummer in de tekst.",
        [
            Citation(title="verzonnen", url="https://edwinvandillen.nl/nergens", source="edwinvandillen.nl"),
            Citation(title="A", url="https://edwinvandillen.nl/a", source="edwinvandillen.nl"),
        ],
        retrieved,
    )
    assert answer == "Geen nummer in de tekst."
    assert [c.url for c in citations] == ["https://edwinvandillen.nl/a"]


if __name__ == "__main__":
    test_slot_five_renumbers_to_first_shown_source()
    test_same_article_keeps_one_number()
    test_without_markers_only_retrieved_urls_remain()
    print("ok")
