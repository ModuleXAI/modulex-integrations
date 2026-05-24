"""Pydantic response models for the metaphor integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "FindSimilarLinksOutput",
    "GetDocumentsContentOutput",
    "SearchOutput",
    "SearchResult",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class SearchResult(_Base):
    """A single search result returned by the Metaphor API."""

    title: str | None = None
    url: str | None = None
    published_date: str | None = None
    author: str | None = None
    id: str | None = None
    score: float | None = None


class DocumentContent(_Base):
    """Content of a document retrieved by ID."""

    id: str | None = None
    url: str | None = None
    title: str | None = None
    extract: str | None = None


# --- Per-action output models ---------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResult] = Field(default_factory=list)
    autoprompt_string: str | None = None


class FindSimilarLinksOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResult] = Field(default_factory=list)


class GetDocumentsContentOutput(_Base):
    success: bool
    error: str | None = None
    contents: list[DocumentContent] = Field(default_factory=list)
