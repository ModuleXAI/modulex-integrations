"""Pydantic response models for the Airtable integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AirtableRecord",
    "CreateRecordsOutput",
    "DeleteRecordsOutput",
    "GetRecordOutput",
    "ListBasesOutput",
    "ListRecordsOutput",
    "ListTablesOutput",
    "UpdateRecordsOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AirtableRecord(_Base):
    id: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    createdTime: str | None = None


class ListBasesOutput(_Base):
    success: bool
    error: str | None = None
    bases: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class ListTablesOutput(_Base):
    success: bool
    error: str | None = None
    tables: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    base_id: str | None = None


class ListRecordsOutput(_Base):
    success: bool
    error: str | None = None
    records: list[AirtableRecord] = Field(default_factory=list)
    count: int = 0
    table: str | None = None
    base_id: str | None = None


class GetRecordOutput(_Base):
    success: bool
    error: str | None = None
    record: AirtableRecord | None = None


class CreateRecordsOutput(_Base):
    success: bool
    error: str | None = None
    records: list[AirtableRecord] = Field(default_factory=list)
    count: int = 0
    table: str | None = None
    base_id: str | None = None


class UpdateRecordsOutput(_Base):
    success: bool
    error: str | None = None
    records: list[AirtableRecord] = Field(default_factory=list)
    count: int = 0
    table: str | None = None
    base_id: str | None = None
    # On partial failure (batch N succeeded, batch N+1 failed), this
    # surfaces how many made it through before the error.
    updated_count: int | None = None


class DeleteRecordsOutput(_Base):
    success: bool
    error: str | None = None
    deleted_ids: list[str] = Field(default_factory=list)
    count: int = 0
    table: str | None = None
    base_id: str | None = None
    deleted_count: int | None = None
