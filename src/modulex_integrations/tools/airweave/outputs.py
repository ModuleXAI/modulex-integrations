"""Pydantic response models for the Airweave integration's @tool functions.

Airweave follows the modulex *api_key* runtime convention: the function
signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it by reading the API key from the resolved ``api_key``
credential.

Error model: non-2xx HTTP responses and timeouts are caught and surfaced
as ``success=False`` + ``error`` rather than raising. Every output model
carries both the success and failure shapes, with permissive
``<type> | None`` fields parsed defensively with ``.get()``.
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
    """A single result row returned by ``search``."""

    entity_id: str | None = None
    source_name: str | None = None
    md_content: str | None = None
    score: float | None = None
    metadata: dict[str, Any] | None = None
    breadcrumbs: list[str] = Field(default_factory=list)
    url: str | None = None


# --- Per-action output models ----------------------------------------------


class SearchOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResultItem] = Field(default_factory=list)
    completion: str | None = None
    total_results: int = 0
