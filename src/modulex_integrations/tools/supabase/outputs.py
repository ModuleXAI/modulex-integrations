"""Pydantic response models for the supabase integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BatchInsertRowsOutput",
    "CountRowsOutput",
    "DeleteRowOutput",
    "InsertRowOutput",
    "RemoteProcedureCallOutput",
    "SelectRowOutput",
    "UpdateRowOutput",
    "UpsertRowOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class SelectRowOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    count: int | None = None
    status: int | None = None
    status_text: str | None = None


class InsertRowOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    status: int | None = None
    status_text: str | None = None


class UpdateRowOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    status: int | None = None
    status_text: str | None = None


class UpsertRowOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    status: int | None = None
    status_text: str | None = None


class DeleteRowOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    status: int | None = None
    status_text: str | None = None


class BatchInsertRowsOutput(_Base):
    success: bool
    error: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    status: int | None = None
    status_text: str | None = None


class RemoteProcedureCallOutput(_Base):
    success: bool
    error: str | None = None
    data: Any = None
    status: int | None = None
    status_text: str | None = None


class CountRowsOutput(_Base):
    success: bool
    error: str | None = None
    count: int | None = None
