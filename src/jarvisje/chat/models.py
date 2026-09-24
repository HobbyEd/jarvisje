"""Structured output models for the LLM response (same call for answer + citations + hints)."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class Citation(BaseModel):
    title: str = Field(..., description="Title of the source document or page")
    url: str = Field(..., description="Full URL to the source")
    source: str | None = Field(None, description="Domain, e.g. edwinvandillen.nl")


class SourceFit(BaseModel):
    """Reader-facing fit of an answer to the indexed articles. Not a truth probability."""

    answer_fit: float | None = Field(
        None, description="1 minus cosine distance of the answer to the nearest chunk, clamped to 0..1."
    )
    question_fit: float | None = Field(
        None, description="Same measure for the user question, from the chunks already retrieved."
    )
    band: str = Field("onbekend", description="sterk, matig, zwak, or onbekend.")
    source_count: int = Field(0, description="Citations the reader actually sees.")
    nearest_title: str | None = Field(
        None, description="Title of the article the answer sits nearest, only when pivot is set."
    )
    pivot: bool = Field(
        False,
        description="Question is far from the blogs and the answer moved closer to an article.",
    )


class ChatResponse(BaseModel):
    """The structured response we ask the LLM to produce in one call."""
    answer: str = Field(..., description="The helpful answer in Dutch, grounded in the retrieved content. Always include citations when making claims.")
    citations: List[Citation] = Field(default_factory=list, description="Concrete sources used. At least one when factual claims are made.")
    hints: List[str] = Field(
        default_factory=list,
        description="3 to 5 short suggested follow-up questions or topics the user might want to explore next.",
        max_length=5,
    )
    role_context: str = "onbekend"
    source_fit: SourceFit | None = None

    @field_validator("role_context", mode="before")
    @classmethod
    def _coerce_role(cls, value: object) -> str:
        if value in ("sollicitant", "bedrijf", "onbekend"):
            return str(value)
        return "onbekend"
