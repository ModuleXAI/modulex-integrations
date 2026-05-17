"""Pydantic response models for the google_sheets integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AddRowsOutput",
    "AddWorksheetOutput",
    "ClearRowsOutput",
    "DeleteRowsOutput",
    "DeleteWorksheetOutput",
    "FindRowsOutput",
    "GetSpreadsheetInfoOutput",
    "GetValuesInRangeOutput",
    "ListSpreadsheetsOutput",
    "ListWorksheetsOutput",
    "NewSpreadsheetOutput",
    "ReadRowsOutput",
    "SpreadsheetSummary",
    "UpdateCellOutput",
    "UpdateRowOutput",
    "WorksheetInfo",
    "WorksheetSummary",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -------------------------------------------------


class SpreadsheetSummary(_Base):
    """A lightweight summary of a Google Sheets spreadsheet."""

    spreadsheet_id: str | None = None
    name: str | None = None
    url: str | None = None


class WorksheetSummary(_Base):
    """A worksheet (tab) summary as returned by list/info actions."""

    sheet_id: int | None = None
    title: str | None = None
    index: int | None = None
    sheet_type: str | None = None
    row_count: int | None = None
    column_count: int | None = None


class WorksheetInfo(_Base):
    """A worksheet summary plus its row-1 headers, used by get_spreadsheet_info."""

    sheet_name: str | None = None
    sheet_id: int | None = None
    row_count: int | None = None
    headers: list[str] | None = None


# --- Per-action output models ----------------------------------------------


class ListSpreadsheetsOutput(_Base):
    success: bool
    error: str | None = None
    spreadsheets: list[SpreadsheetSummary] | None = None
    count: int | None = None


class NewSpreadsheetOutput(_Base):
    success: bool
    error: str | None = None
    spreadsheet_id: str | None = None
    title: str | None = None
    url: str | None = None
    worksheet_name: str | None = None


class GetSpreadsheetInfoOutput(_Base):
    success: bool
    error: str | None = None
    spreadsheet_id: str | None = None
    title: str | None = None
    worksheets: list[WorksheetInfo] | None = None


class ListWorksheetsOutput(_Base):
    success: bool
    error: str | None = None
    worksheets: list[WorksheetSummary] | None = None
    count: int | None = None


class AddWorksheetOutput(_Base):
    success: bool
    error: str | None = None
    sheet_id: int | None = None
    title: str | None = None
    index: int | None = None


class DeleteWorksheetOutput(_Base):
    success: bool
    error: str | None = None
    spreadsheet_id: str | None = None
    deleted_sheet_id: int | None = None


class ReadRowsOutput(_Base):
    success: bool
    error: str | None = None
    headers: list[str] | None = None
    rows: list[Any] | None = None
    row_count: int | None = None


class GetValuesInRangeOutput(_Base):
    success: bool
    error: str | None = None
    range: str | None = None
    values: list[list[Any]] | None = None
    row_count: int | None = None


class FindRowsOutput(_Base):
    success: bool
    error: str | None = None
    matches: list[dict[str, Any]] | None = None
    match_count: int | None = None


class AddRowsOutput(_Base):
    success: bool
    error: str | None = None
    rows_added: int | None = None
    updated_range: str | None = None
    updated_rows: int | None = None
    updated_columns: int | None = None
    updated_cells: int | None = None


class UpdateRowOutput(_Base):
    success: bool
    error: str | None = None
    updated_range: str | None = None
    updated_rows: int | None = None
    updated_columns: int | None = None
    updated_cells: int | None = None


class UpdateCellOutput(_Base):
    success: bool
    error: str | None = None
    updated_range: str | None = None
    updated_cells: int | None = None


class ClearRowsOutput(_Base):
    success: bool
    error: str | None = None
    spreadsheet_id: str | None = None
    cleared_range: str | None = None


class DeleteRowsOutput(_Base):
    success: bool
    error: str | None = None
    spreadsheet_id: str | None = None
    deleted_count: int | None = None
