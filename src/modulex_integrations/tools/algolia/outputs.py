"""Pydantic response models for the algolia integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BrowseRecordsOutput",
    "DeleteRecordsOutput",
    "ListIndexNameOptionsOutput",
    "SaveRecordsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class BrowseRecordsOutput(_Base):
    success: bool
    error: str | None = None
    hits: list[dict[str, Any]] = Field(default_factory=list)
    cursor: str | None = None

class DeleteRecordsOutput(_Base):
    success: bool
    error: str | None = None
    task_id: int | None = None
    object_ids: list[str] = Field(default_factory=list)

class ListIndexNameOptionsOutput(_Base):
    success: bool
    error: str | None = None
    index_names: list[str] = Field(default_factory=list)

class SaveRecordsOutput(_Base):
    success: bool
    error: str | None = None
    task_id: int | None = None
    object_ids: list[str] = Field(default_factory=list)
