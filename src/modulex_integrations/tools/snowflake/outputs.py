"""Pydantic response models for the Snowflake integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BatchResult",
    "DatabaseEntry",
    "DescribeTableOutput",
    "ExecuteSqlQueryOutput",
    "GetTableSampleOutput",
    "InsertMultipleRowsOutput",
    "InsertRowOutput",
    "ListDatabasesOutput",
    "ListSchemasOutput",
    "ListTablesOutput",
    "ListWarehousesOutput",
    "SchemaEntry",
    "TableEntry",
    "WarehouseEntry",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class ExecuteSqlQueryOutput(_Base):
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)


class InsertRowOutput(_Base):
    table: str | None = None
    rows_inserted: int = 0
    columns: list[str] = Field(default_factory=list)


class BatchResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    batch_index: int
    rows_processed: int
    success: bool
    error: str | None = None


class InsertMultipleRowsOutput(_Base):
    table: str | None = None
    total_rows: int = 0
    rows_inserted: int = 0
    total_batches: int = 0
    successful_batches: int = 0
    failed_batches: int = 0
    batch_size: int | None = None
    batch_results: list[BatchResult] = Field(default_factory=list)


class DatabaseEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    owner: str | None = None
    created_on: str | None = None
    comment: str | None = None


class ListDatabasesOutput(_Base):
    databases: list[DatabaseEntry] = Field(default_factory=list)
    count: int = 0


class SchemaEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    database_name: str | None = None
    owner: str | None = None
    created_on: str | None = None
    comment: str | None = None


class ListSchemasOutput(_Base):
    database: str | None = None
    schemas: list[SchemaEntry] = Field(default_factory=list)
    count: int = 0


class TableEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    database_name: str | None = None
    schema_name: str | None = None
    kind: str | None = None
    owner: str | None = None
    rows: int | None = None
    created_on: str | None = None
    comment: str | None = None


class ListTablesOutput(_Base):
    database: str | None = None
    schema_name: str | None = None
    tables: list[TableEntry] = Field(default_factory=list)
    count: int = 0


class WarehouseEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = None
    state: str | None = None
    size: str | None = None
    type: str | None = None
    owner: str | None = None
    auto_suspend: int | None = None
    auto_resume: bool | str | None = None
    created_on: str | None = None
    comment: str | None = None


class ListWarehousesOutput(_Base):
    warehouses: list[WarehouseEntry] = Field(default_factory=list)
    count: int = 0


class DescribeTableOutput(_Base):
    table: str | None = None
    columns: list[dict[str, Any]] = Field(default_factory=list)
    column_count: int = 0


class GetTableSampleOutput(_Base):
    table: str | None = None
    row_count: int = 0
    data: list[dict[str, Any]] = Field(default_factory=list)
