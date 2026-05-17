"""Pydantic response models for the AppDrag integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ExecuteApiFunctionOutput",
    "InsertRowOutput",
    "UpdateRowOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ExecuteApiFunctionOutput(_Base):
    success: bool
    error: str | None = None
    path: str | None = None
    method: str | None = None
    # response is whatever the upstream function returned: JSON object,
    # string, list — we don't constrain it.
    response: Any = None


class InsertRowOutput(_Base):
    success: bool
    error: str | None = None
    table: str | None = None
    columns: list[str] = Field(default_factory=list)
    affected_rows: int = 0
    response: dict[str, Any] | None = None


class UpdateRowOutput(_Base):
    success: bool
    error: str | None = None
    table: str | None = None
    columns_updated: list[str] = Field(default_factory=list)
    affected_rows: int = 0
    response: dict[str, Any] | None = None
