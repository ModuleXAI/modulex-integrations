"""Pydantic response models for the Linkup integration's @tool functions.

Linkup follows the modulex *api_key* runtime convention: the function
signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it from the resolved ``api_key`` credential.

Error model: non-2xx responses, timeouts, and unexpected exceptions are
caught and surfaced as ``success=False`` + ``error`` rather than raising.
Every output model carries both shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "SearchOutput",
    "SearchResultItem",
    "SearchSource",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class SearchSource(_Base):
    """A citation in a ``sourcedAnswer`` response's ``sources`` array."""

    name: str | None = None
    url: str | None = None
    snippet: str | None = None


class SearchResultItem(_Base):
    """A single result row in a ``searchResults`` response."""

    type: str | None = None
    name: str | None = None
    url: str | None = None
    content: str | None = None


# --- Per-action output models ----------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    # Populated when ``output_type`` is ``sourcedAnswer``.
    answer: str | None = None
    sources: list[SearchSource] = Field(default_factory=list)
    # Populated when ``output_type`` is ``searchResults``.
    results: list[SearchResultItem] = Field(default_factory=list)
    # Populated when ``output_type`` is ``structured`` (shape is defined by
    # the caller's JSON schema, so it is returned verbatim).
    structured_data: dict[str, Any] | None = None
