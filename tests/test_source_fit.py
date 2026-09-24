"""Bronpassing bands from the three answers measured on 2026-09-24."""
from jarvisje.chat.source_fit import assess_source_fit, similarity


def test_glossarium_answer_is_strong_without_pivot():
    fit = assess_source_fit(question_distance=0.35, answer_distance=0.1282, source_count=2)
    assert fit.band == "sterk"
    assert fit.source_count == 2
    assert fit.pivot is False
    assert fit.answer_fit is not None and fit.answer_fit > 0.85


def test_hoxha_answer_is_fair_and_pivots_without_sources():
    fit = assess_source_fit(
        question_distance=0.5609,
        answer_distance=0.379,
        source_count=0,
        nearest_title="De deal die Hormuz nog steeds regeert",
    )
    assert fit.band == "matig"
    assert fit.source_count == 0
    assert fit.pivot is True
    assert fit.nearest_title.startswith("De deal")


def test_joke_answer_is_weak_and_does_not_pivot():
    fit = assess_source_fit(question_distance=0.4899, answer_distance=0.5211, source_count=0)
    assert fit.band == "zwak"
    assert fit.pivot is False
    assert fit.nearest_title is None


def test_missing_answer_distance_stays_unknown():
    fit = assess_source_fit(question_distance=0.35, answer_distance=None, source_count=1)
    assert fit.band == "onbekend"
    assert fit.answer_fit is None
    assert fit.pivot is False
    assert fit.source_count == 1


def test_similarity_clamps():
    assert similarity(0.0) == 1.0
    assert similarity(1.2) == 0.0
    assert similarity(None) is None
