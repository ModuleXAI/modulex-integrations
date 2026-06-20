"""Pydantic response models for the Mem0 integration's @tool functions.

Mem0 follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly, which the modulex
``ToolExecutor`` injects from the resolved credential.

Error model: non-2xx responses, timeouts, and unexpected exceptions are
caught and surfaced as ``success=False`` + ``error`` rather than raising.
Every output model carries both shapes — on success the data fields are
populated, on failure they stay at their permissive defaults.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddMemoriesOutput",
    "GetMemoriesOutput",
    "MemoryRecord",
    "SearchMemoriesOutput",
    "SearchResultRecord",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class MemoryRecord(_Base):
    """A single memory object returned by ``get_memories``."""

    id: str | None = None
    memory: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    app_id: str | None = None
    run_id: str | None = None
    hash: str | None = None
    metadata: dict[str, Any] | None = None
    categories: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


class SearchResultRecord(_Base):
    """A single ranked result returned by ``search_memories``."""

    id: str | None = None
    memory: str | None = None
    user_id: str | None = None
    agent_id: str | None = None
    app_id: str | None = None
    run_id: str | None = None
    hash: str | None = None
    metadata: dict[str, Any] | None = None
    categories: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    score: float | None = None


# --- Per-action output models ----------------------------------------------


class AddMemoriesOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None
    status: str | None = None
    event_id: str | None = None


class SearchMemoriesOutput(_Base):
    success: bool
    error: str | None = None
    search_results: list[SearchResultRecord] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)


class GetMemoriesOutput(_Base):
    success: bool
    error: str | None = None
    memories: list[MemoryRecord] = Field(default_factory=list)
    ids: list[str] = Field(default_factory=list)
    count: int | None = None
    next: str | None = None
    previous: str | None = None
