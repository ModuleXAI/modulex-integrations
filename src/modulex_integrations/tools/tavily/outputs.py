"""Pydantic response models for the Tavily integration's @tool functions.

Tavily is the first migrated **SDK-based** integration: instead of
making raw HTTP calls, each tool instantiates
``langchain_tavily.TavilySearch`` and invokes it. The pydantic output
models still describe the shape — derived from Tavily's documented
search response — so the runtime can produce JSONSchema for the LLM
consistently with HTTP-based tools.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AnswerSearchOutput",
    "NewsSearchOutput",
    "TavilyResult",
    "WebSearchOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TavilyResult(_Base):
    """One row in a Tavily search response."""

    url: str | None = None
    title: str | None = None
    content: str | None = None
    score: float | None = None
    raw_content: str | None = None


class WebSearchOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    answer: str | None = None
    results: list[TavilyResult] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    response_time: float | None = None
    request_id: str | None = None


class AnswerSearchOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    answer: str | None = None
    results: list[TavilyResult] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    response_time: float | None = None
    request_id: str | None = None


class NewsSearchOutput(_Base):
    success: bool
    error: str | None = None
    query: str | None = None
    results: list[TavilyResult] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    response_time: float | None = None
    request_id: str | None = None
