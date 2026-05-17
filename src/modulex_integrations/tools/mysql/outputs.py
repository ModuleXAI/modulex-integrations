"""Pydantic response models for the MySQL integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateRowOutput",
    "DeleteRowOutput",
    "DescribeTableOutput",
    "ExecuteQueryWithConditionOutput",
    "ExecuteRawQueryOutput",
    "ExecuteStoredProcedureOutput",
    "FindRowOutput",
    "ListTablesOutput",
    "TableEntry",
    "UpdateRowOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class ExecuteRawQueryOutput(_Base):
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)


class CreateRowOutput(_Base):
    table: str | None = None
    affected_rows: int = 0
    last_insert_id: int | None = None
    columns: list[str] = Field(default_factory=list)


class DeleteRowOutput(_Base):
    table: str | None = None
    affected_rows: int = 0


class UpdateRowOutput(_Base):
    table: str | None = None
    affected_rows: int = 0
    updated_columns: list[str] = Field(default_factory=list)


class FindRowOutput(_Base):
    table: str | None = None
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)


class ExecuteQueryWithConditionOutput(_Base):
    table: str | None = None
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)


class ExecuteStoredProcedureOutput(_Base):
    procedure: str | None = None
    row_count: int = 0
    data: list[dict[str, Any]] | dict[str, Any] | None = None


class TableEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    type: str | None = None


class ListTablesOutput(_Base):
    database: str | None = None
    tables: list[TableEntry] = Field(default_factory=list)
    count: int = 0


class DescribeTableOutput(_Base):
    table: str | None = None
    columns: list[dict[str, Any]] = Field(default_factory=list)
    column_count: int = 0
