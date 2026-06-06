"""Pydantic response models for the Google Drive integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddSlideOutput",
    "AppendToGoogleDocOutput",
    "CreateFolderOutput",
    "CreateGoogleDocOutput",
    "CreateGoogleSheetOutput",
    "CreateGoogleSlidesOutput",
    "CreateTextFileOutput",
    "FormatSheetCellsOutput",
    "FormatSheetTextOutput",
    "ReadGoogleDocOutput",
    "ReadGoogleSheetOutput",
    "ReadGoogleSlidesOutput",
    "UpdateGoogleDocOutput",
    "UpdateGoogleSheetOutput",
    "UpdateSlideContentOutput",
    "UpdateTextFileOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class CreateTextFileOutput(_Base):
    id: str | None = None
    name: str | None = None
    mime_type: str | None = None
    web_view_link: str | None = None


class UpdateTextFileOutput(_Base):
    id: str | None = None
    name: str | None = None
    mime_type: str | None = None
    modified_time: str | None = None
    web_view_link: str | None = None


class CreateFolderOutput(_Base):
    id: str | None = None
    name: str | None = None
    web_view_link: str | None = None


class CreateGoogleDocOutput(_Base):
    id: str | None = None
    name: str | None = None
    web_view_link: str | None = None


class ReadGoogleDocOutput(_Base):
    id: str | None = None
    title: str | None = None
    content: str | None = None
    revision_id: str | None = None


class UpdateGoogleDocOutput(_Base):
    id: str | None = None
    title: str | None = None
    message: str | None = None


class AppendToGoogleDocOutput(_Base):
    id: str | None = None
    title: str | None = None
    message: str | None = None


class CreateGoogleSheetOutput(_Base):
    id: str | None = None
    name: str | None = None
    web_view_link: str | None = None


class ReadGoogleSheetOutput(_Base):
    spreadsheet_id: str | None = None
    range: str | None = None
    values: list[list[Any]] = Field(default_factory=list)
    row_count: int = 0


class UpdateGoogleSheetOutput(_Base):
    spreadsheet_id: str | None = None
    updated_range: str | None = None
    updated_rows: int | None = None
    updated_columns: int | None = None
    updated_cells: int | None = None


class FormatSheetCellsOutput(_Base):
    spreadsheet_id: str | None = None
    range: str | None = None
    message: str | None = None


class FormatSheetTextOutput(_Base):
    spreadsheet_id: str | None = None
    range: str | None = None
    message: str | None = None


class CreateGoogleSlidesOutput(_Base):
    id: str | None = None
    name: str | None = None
    web_view_link: str | None = None


class ReadGoogleSlidesOutput(_Base):
    id: str | None = None
    title: str | None = None
    slide_count: int = 0
    slides: list[dict[str, Any]] = Field(default_factory=list)


class AddSlideOutput(_Base):
    presentation_id: str | None = None
    slide_id: str | None = None
    layout: str | None = None
    message: str | None = None


class UpdateSlideContentOutput(_Base):
    presentation_id: str | None = None
    slide_id: str | None = None
    placeholder_id: str | None = None
    message: str | None = None
