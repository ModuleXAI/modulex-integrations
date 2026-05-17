"""Pydantic response models for the Exa integration's @tool functions.

Exa's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair used by github/slack), and the modulex
``ToolExecutor`` injects it by reading the API key from the resolved
``api_key`` or ``modulex_key`` credential.

Error model: Exa returns proper HTTP status codes, but the legacy
modulex tool wraps everything in a try/except so non-2xx and timeouts
surface as ``success=False`` + ``error`` rather than exceptions. We
preserve that behavior — every output model carries both shapes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AnswerOutput",
    "AnswerSource",
    "ContentItem",
    "FindSimilarOutput",
    "GetContentsOutput",
    "SearchOutput",
    "SearchResultItem",
    "SimilarResultItem",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class SearchResultItem(_Base):
    """A single result row in ``search``."""

    title: str | None = None
    url: str | None = None
    published_date: str | None = None
    author: str | None = None
    score: float | None = None
    text: str | None = None
    highlights: list[str] = Field(default_factory=list)
    summary: str | None = None


class ContentItem(_Base):
    """A single result row in ``get_contents``."""

    url: str | None = None
    title: str | None = None
    published_date: str | None = None
    author: str | None = None
    text: str | None = None
    highlights: list[str] = Field(default_factory=list)
    summary: str | None = None


class SimilarResultItem(_Base):
    """A single result row in ``find_similar``."""

    title: str | None = None
    url: str | None = None
    published_date: str | None = None
    author: str | None = None
    score: float | None = None
    text: str | None = None


class AnswerSource(_Base):
    """A single citation in ``answer``'s sources list."""

    title: str | None = None
    url: str | None = None
    published_date: str | None = None


# --- Per-action output models ----------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResultItem] = Field(default_factory=list)
    total_results: int = 0
    search_type: str | None = None
    request_id: str | None = None


class GetContentsOutput(_Base):
    success: bool
    error: str | None = None
    results: list[ContentItem] = Field(default_factory=list)
    total_results: int = 0
    request_id: str | None = None


class FindSimilarOutput(_Base):
    success: bool
    error: str | None = None
    source_url: str | None = None
    results: list[SimilarResultItem] = Field(default_factory=list)
    total_results: int = 0
    request_id: str | None = None


class AnswerOutput(_Base):
    success: bool
    error: str | None = None
    answer: str | None = None
    sources: list[AnswerSource] = Field(default_factory=list)
    request_id: str | None = None
