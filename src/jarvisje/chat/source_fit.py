"""How closely an answer sits next to the blogs.

Chroma cosine distance on normalized vectors is 1 minus cosine similarity.
Bronpassing is that similarity, clamped to 0..1. Higher means the text lies
closer to some indexed chunk. Bands are provisional; see ADR-013.
"""
from __future__ import annotations

from .models import SourceFit

# Measured 2026-09-24: glossarium answer 0.87, Hoxha answer 0.62, joke 0.48.
STRONG_AT = 0.75
FAIR_AT = 0.55
# Pivot sentence: the question itself is far, and the answer moved toward an article.
PIVOT_QUESTION_BELOW = 0.55
PIVOT_GAP = 0.10


def similarity(distance: float | None) -> float | None:
    if distance is None:
        return None
    value = 1.0 - float(distance)
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def band_for(answer_fit: float | None) -> str:
    if answer_fit is None:
        return "onbekend"
    if answer_fit >= STRONG_AT:
        return "sterk"
    if answer_fit >= FAIR_AT:
        return "matig"
    return "zwak"


def best_distance(distances: list[float | None]) -> float | None:
    values = [float(d) for d in distances if d is not None]
    if not values:
        return None
    return min(values)


def assess_source_fit(
    question_distance: float | None,
    answer_distance: float | None,
    source_count: int,
    nearest_title: str | None = None,
) -> SourceFit:
    question_fit = similarity(question_distance)
    answer_fit = similarity(answer_distance)
    pivot = (
        question_fit is not None
        and answer_fit is not None
        and question_fit < PIVOT_QUESTION_BELOW
        and (answer_fit - question_fit) >= PIVOT_GAP
    )
    title = (nearest_title or "").strip() or None
    return SourceFit(
        answer_fit=answer_fit,
        question_fit=question_fit,
        band=band_for(answer_fit),
        source_count=max(0, int(source_count)),
        nearest_title=title if pivot else None,
        pivot=pivot,
    )
