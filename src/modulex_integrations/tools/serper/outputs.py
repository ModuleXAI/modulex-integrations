"""Pydantic response models for the Serper integration's @tool functions.

Serper follows the *api_key* runtime convention: the ``search``
function takes ``api_key: str`` directly and the modulex
``ToolExecutor`` injects it from the resolved credential.

Error model: every output model carries ``success: bool`` +
``error: str | None``. Non-2xx responses, timeouts, and unexpected
exceptions are caught and surfaced as ``success=False`` rather than
raising. Data fields stay permissive (``.get()`` everywhere) to
preserve whatever the upstream API returns.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "SearchOutput",
    "SearchResultItem",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class SearchResultItem(_Base):
    """A single unified result row.

    The populated fields depend on the search ``type``:
    web/organic results carry title/link/snippet/position; news adds
    ``date`` and ``image_url``; places add ``rating``/``reviews``/
    ``address``; images add ``image_url``.
    """

    title: str | None = None
    link: str | None = None
    snippet: str | None = None
    position: int | None = None
    date: str | None = None
    image_url: str | None = None
    source: str | None = None
    rating: float | None = None
    reviews: int | None = None
    address: str | None = None
    price: str | None = None
    duration: str | None = None


# --- Per-action output models ----------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    search_type: str | None = None
    search_results: list[SearchResultItem] = Field(default_factory=list)
    # Rich SERP blocks present on web ("search") responses. Kept
    # permissive — the upstream API returns these only when relevant.
    knowledge_graph: dict[str, Any] | None = None
    answer_box: dict[str, Any] | None = None
    people_also_ask: list[dict[str, Any]] = Field(default_factory=list)
    related_searches: list[dict[str, Any]] = Field(default_factory=list)
    top_stories: list[dict[str, Any]] = Field(default_factory=list)
