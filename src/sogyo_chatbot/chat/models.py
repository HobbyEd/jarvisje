"""Structured output models for the LLM response (same call for answer + citations + hints)."""
from __future__ import annotations

from typing import List, Literal

from pydantic import BaseModel, Field


class Citation(BaseModel):
    title: str = Field(..., description="Title of the source document or page")
    url: str = Field(..., description="Full URL to the source")
    source: str | None = Field(None, description="Domain or collection name, e.g. sogyo.nl")


class ChatResponse(BaseModel):
    """The structured response we ask the LLM to produce in one call."""
    answer: str = Field(..., description="The helpful answer in Dutch, grounded in the retrieved content. Always include citations when making claims.")
    citations: List[Citation] = Field(default_factory=list, description="Concrete sources used. At least one when factual claims are made.")
    hints: List[str] = Field(
        default_factory=list,
        description="3 to 5 short suggested follow-up questions or topics the user might want to explore next.",
        max_length=5,
    )
    role_context: Literal["sollicitant", "bedrijf", "onbekend"] = "onbekend"
