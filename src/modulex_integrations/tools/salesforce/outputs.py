"""Pydantic response models for the Salesforce integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddContactToCampaignOutput",
    "AddLeadToCampaignOutput",
    "CreateAccountOutput",
    "CreateCaseOutput",
    "CreateContactOutput",
    "CreateLeadOutput",
    "CreateOpportunityOutput",
    "CreateRecordOutput",
    "CreateTaskOutput",
    "DeleteRecordOutput",
    "DescribeObjectOutput",
    "GetRecordOutput",
    "ListObjectsOutput",
    "SoqlQueryOutput",
    "SoslSearchOutput",
    "UpdateRecordOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class SoqlQueryOutput(_Base):
    total_size: int = 0
    done: bool = True
    next_records_url: str | None = None
    records: list[dict[str, Any]] = Field(default_factory=list)


class SoslSearchOutput(_Base):
    search_records: Any = None


class GetRecordOutput(_Base):
    result: dict[str, Any] | None = None


class _CreateBase(_Base):
    id: str | None = None
    object_type: str | None = None
    created: bool = True


class CreateRecordOutput(_CreateBase):
    pass


class UpdateRecordOutput(_Base):
    id: str | None = None
    object_type: str | None = None
    updated: bool = False


class DeleteRecordOutput(_Base):
    id: str | None = None
    object_type: str | None = None
    deleted: bool = False


class CreateAccountOutput(_Base):
    id: str | None = None
    name: str | None = None
    created: bool = True


class CreateContactOutput(_Base):
    id: str | None = None
    last_name: str | None = None
    created: bool = True


class CreateLeadOutput(_Base):
    id: str | None = None
    last_name: str | None = None
    company: str | None = None
    created: bool = True


class CreateOpportunityOutput(_Base):
    id: str | None = None
    name: str | None = None
    created: bool = True


class CreateTaskOutput(_Base):
    id: str | None = None
    subject: str | None = None
    created: bool = True


class CreateCaseOutput(_Base):
    id: str | None = None
    subject: str | None = None
    created: bool = True


class AddContactToCampaignOutput(_Base):
    id: str | None = None
    campaign_id: str | None = None
    contact_id: str | None = None
    created: bool = True


class AddLeadToCampaignOutput(_Base):
    id: str | None = None
    campaign_id: str | None = None
    lead_id: str | None = None
    created: bool = True


class DescribeObjectOutput(_Base):
    name: str | None = None
    label: str | None = None
    key_prefix: str | None = None
    createable: bool | None = None
    updateable: bool | None = None
    deletable: bool | None = None
    queryable: bool | None = None
    searchable: bool | None = None
    fields: list[dict[str, Any]] = Field(default_factory=list)
    field_count: int = 0


class ListObjectsOutput(_Base):
    objects: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
