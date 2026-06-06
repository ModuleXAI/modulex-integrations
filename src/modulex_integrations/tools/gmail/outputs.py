"""Pydantic response models for the Gmail integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ListLabelsOutput",
    "SendMessageOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class SendMessageOutput(_Base):
    id: str | None = None
    thread_id: str | None = None
    label_ids: list[str] = Field(default_factory=list)


class ListLabelsOutput(_Base):
    labels: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
