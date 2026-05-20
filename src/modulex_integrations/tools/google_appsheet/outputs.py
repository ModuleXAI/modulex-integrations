"""Pydantic response models for the google_appsheet integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddRowOutput",
    "DeleteRowOutput",
    "GetRowsOutput",
    "UpdateRowOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class AddRowOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)


class DeleteRowOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)


class GetRowsOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)


class UpdateRowOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[dict[str, Any]] = Field(default_factory=list)
