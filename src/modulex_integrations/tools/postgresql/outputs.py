"""Pydantic response models for the PostgreSQL integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateRowOutput",
    "DeleteRowOutput",
    "DescribeTableOutput",
    "ExecuteQueryWithConditionOutput",
    "ExecuteRawQueryOutput",
    "FindRowOutput",
    "ListSchemasOutput",
    "ListTablesOutput",
    "TableEntry",
    "UpdateRowOutput",
    "UpsertRowOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class ExecuteRawQueryOutput(_Base):
    row_count: int | None = None
    data: list[dict[str, Any]] | None = None
    status: str | None = None
    affected_rows: int | None = None


class CreateRowOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    inserted_row: dict[str, Any] | None = None
    columns: list[str] | None = None


class DeleteRowOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    affected_rows: int = 0
    deleted_rows: list[dict[str, Any]] = Field(default_factory=list)


class UpdateRowOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    affected_rows: int = 0
    updated_columns: list[str] = Field(default_factory=list)
    updated_rows: list[dict[str, Any]] = Field(default_factory=list)


class UpsertRowOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    upserted_row: dict[str, Any] | None = None
    conflict_target: str | None = None


class FindRowOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)


class ExecuteQueryWithConditionOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)


class ListSchemasOutput(_Base):
    schemas: list[str] = Field(default_factory=list)
    count: int = 0


class TableEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    type: str | None = None


class ListTablesOutput(_Base):
    schema_name: str | None = None
    tables: list[TableEntry] = Field(default_factory=list)
    count: int = 0


class DescribeTableOutput(_Base):
    table: str | None = None
    schema_name: str | None = None
    columns: list[dict[str, Any]] = Field(default_factory=list)
    column_count: int = 0
    primary_keys: list[str] = Field(default_factory=list)
