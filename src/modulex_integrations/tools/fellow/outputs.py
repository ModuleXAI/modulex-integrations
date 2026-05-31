"""Pydantic response models for the fellow integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ArchiveActionItemOutput",
    "CompleteActionItemOutput",
    "GetNoteByIdOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class ArchiveActionItemOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CompleteActionItemOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetNoteByIdOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None
