"""Pydantic response models for the typeform integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateFormOutput",
    "CreateImageOutput",
    "DeleteFormOutput",
    "DeleteImageOutput",
    "DuplicateFormOutput",
    "FormSummary",
    "GetFormOutput",
    "ImageItem",
    "ListFormsOutput",
    "ListImagesOutput",
    "ListResponsesOutput",
    "LookupResponsesOutput",
    "ResponseItem",
    "UpdateDropdownMultipleChoiceRankingOutput",
    "UpdateFormTitleOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class FormSummary(_Base):
    id: str | None = None
    title: str | None = None
    type: str | None = None
    last_updated_at: str | None = None
    self_url: str | None = None


class ResponseItem(_Base):
    response_id: str | None = None
    landed_at: str | None = None
    submitted_at: str | None = None
    answers: list[dict[str, Any]] = Field(default_factory=list)


class ImageItem(_Base):
    id: str | None = None
    src: str | None = None
    file_name: str | None = None
    width: int | None = None
    height: int | None = None


# --- Per-action output models ---------------------------------------------


class ListFormsOutput(_Base):
    success: bool
    error: str | None = None
    forms: list[FormSummary] = Field(default_factory=list)
    total_items: int | None = None
    page_count: int | None = None


class CreateFormOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    type: str | None = None
    self_url: str | None = None


class DuplicateFormOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    type: str | None = None
    self_url: str | None = None


class DeleteFormOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class ListImagesOutput(_Base):
    success: bool
    error: str | None = None
    images: list[ImageItem] = Field(default_factory=list)


class GetFormOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    type: str | None = None
    fields: list[dict[str, Any]] = Field(default_factory=list)
    self_url: str | None = None


class LookupResponsesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ResponseItem] = Field(default_factory=list)
    total_items: int | None = None
    page_count: int | None = None


class ListResponsesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[ResponseItem] = Field(default_factory=list)
    total_items: int | None = None
    page_count: int | None = None


class UpdateFormTitleOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None


class DeleteImageOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class CreateImageOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    src: str | None = None
    file_name: str | None = None
    width: int | None = None
    height: int | None = None


class UpdateDropdownMultipleChoiceRankingOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    fields: list[dict[str, Any]] = Field(default_factory=list)
