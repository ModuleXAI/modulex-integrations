"""Pydantic response models for the mintlify integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ChatWithAssistantOutput",
    "SearchDocumentationOutput",
    "SearchResultItem",
    "TriggerUpdateOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class SearchResultItem(_Base):
    """A single search result from the documentation."""

    title: str | None = None
    url: str | None = None
    content: str | None = None
    score: float | None = None


# --- Per-action output models ---------------------------------------------


class ChatWithAssistantOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    response: Any | None = None


class SearchDocumentationOutput(_Base):
    success: bool
    error: str | None = None
    results: list[SearchResultItem] = Field(default_factory=list)
    total: int | None = None


class TriggerUpdateOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
