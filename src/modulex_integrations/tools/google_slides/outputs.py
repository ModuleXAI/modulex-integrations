"""Pydantic response models for the google_slides integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateImageOutput",
    "CreatePageElementOutput",
    "CreatePresentationOutput",
    "CreateSlideOutput",
    "CreateTableOutput",
    "DeletePageElementOutput",
    "DeleteSlideOutput",
    "DeleteTableColumnOutput",
    "DeleteTableRowOutput",
    "FindPresentationOutput",
    "InsertTableColumnsOutput",
    "InsertTableRowsOutput",
    "InsertTextIntoTableOutput",
    "InsertTextOutput",
    "MergeDataOutput",
    "RefreshChartOutput",
    "ReplaceAllTextOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Per-action output models ----------------------------------------------


class CreateImageOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    image_object_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class CreatePageElementOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    shape_object_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class CreatePresentationOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    title: str | None = None
    revision_id: str | None = None
    copied_from: str | None = None
    file_id: str | None = None
    web_view_link: str | None = None
    raw: dict[str, Any] | None = None


class CreateSlideOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    slide_object_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class CreateTableOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    table_object_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class DeletePageElementOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    deleted_object_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class DeleteSlideOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    deleted_slide_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class DeleteTableColumnOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class DeleteTableRowOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class FindPresentationOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    title: str | None = None
    locale: str | None = None
    revision_id: str | None = None
    page_size: dict[str, Any] | None = None
    slides: list[dict[str, Any]] = Field(default_factory=list)
    layouts: list[dict[str, Any]] = Field(default_factory=list)
    masters: list[dict[str, Any]] = Field(default_factory=list)
    notes_master: dict[str, Any] | None = None
    raw: dict[str, Any] | None = None


class InsertTableColumnsOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class InsertTableRowsOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class InsertTextIntoTableOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class InsertTextOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class MergeDataOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    copied_from_id: str | None = None
    new_presentation_title: str | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None


class RefreshChartOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    refreshed_chart_count: int = 0
    refreshed_chart_ids: list[str] = Field(default_factory=list)


class ReplaceAllTextOutput(_Base):
    success: bool
    error: str | None = None
    presentation_id: str | None = None
    total_occurrences_changed: int | None = None
    replies: list[dict[str, Any]] = Field(default_factory=list)
    write_control: dict[str, Any] | None = None
