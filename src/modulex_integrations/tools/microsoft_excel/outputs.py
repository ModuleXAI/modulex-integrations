"""Pydantic response models for the microsoft_excel integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddAWorksheetTablerowOutput",
    "AddRowOutput",
    "FindRowOutput",
    "FolderOption",
    "GetColumnsOutput",
    "GetSpreadsheetOutput",
    "GetTableRowsOutput",
    "ListFolderIdOptionsOutput",
    "TableRow",
    "UpdateCellOutput",
    "UpdateWorksheetTablerowOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class FolderOption(_Base):
    """One folder option returned by list_folder_id_options."""

    value: str | None = None
    label: str | None = None


class TableRow(_Base):
    """One Microsoft Graph workbookTableRow returned by table operations."""

    index: int | None = None
    values: list[list[Any]] = Field(default_factory=list)


# --- Per-action output models ----------------------------------------------


class AddAWorksheetTablerowOutput(_Base):
    success: bool
    error: str | None = None
    row: TableRow | None = None


class AddRowOutput(_Base):
    success: bool
    error: str | None = None
    address: str | None = None
    values: list[list[Any]] = Field(default_factory=list)


class FindRowOutput(_Base):
    success: bool
    error: str | None = None
    found: bool = False
    row_number: int | None = None
    address: str | None = None
    values: list[list[Any]] = Field(default_factory=list)
    column_values: list[Any] = Field(default_factory=list)


class GetColumnsOutput(_Base):
    success: bool
    error: str | None = None
    values: dict[str, list[Any]] = Field(default_factory=dict)


class GetSpreadsheetOutput(_Base):
    success: bool
    error: str | None = None
    address: str | None = None
    row_count: int | None = None
    column_count: int | None = None
    values: list[list[Any]] = Field(default_factory=list)


class GetTableRowsOutput(_Base):
    success: bool
    error: str | None = None
    rows: list[TableRow] = Field(default_factory=list)


class ListFolderIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[FolderOption] = Field(default_factory=list)


class UpdateCellOutput(_Base):
    success: bool
    error: str | None = None
    address: str | None = None
    values: list[list[Any]] = Field(default_factory=list)


class UpdateWorksheetTablerowOutput(_Base):
    success: bool
    error: str | None = None
    row: TableRow | None = None
