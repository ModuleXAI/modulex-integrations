"""Pydantic response models for the ServiceNow integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateCaseOutput",
    "CreateIncidentOutput",
    "CreateTableRecordOutput",
    "DeleteTableRecordOutput",
    "GetTableRecordOutput",
    "GetTableRecordsOutput",
    "UpdateTableRecordOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class CreateCaseOutput(_Base):
    # Upstream returns the full trouble-ticket payload; preserve unchanged.
    result: dict[str, Any] | None = None


class CreateIncidentOutput(_Base):
    result: dict[str, Any] | None = None


class CreateTableRecordOutput(_Base):
    table: str | None = None
    record: dict[str, Any] | None = None


class GetTableRecordOutput(_Base):
    table: str | None = None
    sys_id: str | None = None
    record: dict[str, Any] | None = None


class GetTableRecordsOutput(_Base):
    table: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class UpdateTableRecordOutput(_Base):
    table: str | None = None
    sys_id: str | None = None
    record: dict[str, Any] | None = None


class DeleteTableRecordOutput(_Base):
    table: str | None = None
    sys_id: str | None = None
