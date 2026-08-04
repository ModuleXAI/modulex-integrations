"""Pydantic response models for the ArXiv integration's @tool functions.

The arXiv API (``export.arxiv.org/api/query``) answers every request with
an Atom 1.0 feed rather than JSON, so each model here describes the
*parsed* shape produced by ``tools.py`` — not a raw upstream payload.

Error model: the arXiv API signals failures two ways — a non-2xx HTTP
status (e.g. ``429 Rate exceeded.``) and a ``200`` Atom feed carrying a
single error ``<entry>``. Both are caught and surfaced as
``success=False`` + ``error`` rather than raising, so every output model
carries the same envelope.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ArxivPaper",
    "GetAuthorPapersOutput",
    "GetPaperOutput",
    "SearchOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class ArxivPaper(_Base):
    """One paper, parsed from a single Atom ``<entry>`` element."""

    id: str | None = None
    title: str | None = None
    summary: str | None = None
    authors: list[str] = Field(default_factory=list)
    published: str | None = None
    updated: str | None = None
    link: str | None = None
    pdf_link: str | None = None
    categories: list[str] = Field(default_factory=list)
    primary_category: str | None = None
    comment: str | None = None
    journal_ref: str | None = None
    doi: str | None = None


# --- Per-action output models ----------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    papers: list[ArxivPaper] = Field(default_factory=list)
    total_results: int = 0
    query: str | None = None


class GetPaperOutput(_Base):
    success: bool
    error: str | None = None
    paper: ArxivPaper | None = None


class GetAuthorPapersOutput(_Base):
    success: bool
    error: str | None = None
    author_papers: list[ArxivPaper] = Field(default_factory=list)
    total_results: int = 0
    author_name: str | None = None
