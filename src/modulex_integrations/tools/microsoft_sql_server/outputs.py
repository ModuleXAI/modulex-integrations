"""Pydantic response models for the microsoft_sql_server integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ExecuteQueryOutput",
    "ExecuteRawQueryOutput",
    "InsertRowOutput",
    "ListTableOptionsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class ExecuteRawQueryOutput(_Base):
    success: bool
    error: str | None = None
    recordset: list[dict[str, Any]] = Field(default_factory=list)
    rows_affected: list[int] = Field(default_factory=list)


class ExecuteQueryOutput(_Base):
    success: bool
    error: str | None = None
    recordset: list[dict[str, Any]] = Field(default_factory=list)
    rows_affected: list[int] = Field(default_factory=list)


class InsertRowOutput(_Base):
    success: bool
    error: str | None = None
    rows_affected: list[int] = Field(default_factory=list)


class ListTableOptionsOutput(_Base):
    success: bool
    error: str | None = None
    tables: list[str] = Field(default_factory=list)
