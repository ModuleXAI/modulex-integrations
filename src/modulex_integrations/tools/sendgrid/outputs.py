"""Pydantic response models for the SendGrid integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddEmailToGlobalSuppressionOutput",
    "AddOrUpdateContactOutput",
    "ContactSummary",
    "CreateContactListOutput",
    "DeleteBlocksOutput",
    "DeleteBouncesOutput",
    "DeleteContactsOutput",
    "DeleteGlobalSuppressionOutput",
    "GetAllBouncesOutput",
    "GetContactListsOutput",
    "ListBlocksOutput",
    "ListGlobalSuppressionsOutput",
    "ListSummary",
    "RemoveContactFromListOutput",
    "SearchContactsOutput",
    "SendEmailMultipleRecipientsOutput",
    "SendEmailOutput",
    "SuppressionRow",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class SendEmailOutput(_Base):
    message: str | None = None
    to: str | None = None
    subject: str | None = None
    message_id: str | None = None


class SendEmailMultipleRecipientsOutput(_Base):
    message: str | None = None
    recipient_count: int = 0
    recipients: list[str] = Field(default_factory=list)
    subject: str | None = None
    message_id: str | None = None


class AddOrUpdateContactOutput(_Base):
    message: str | None = None
    job_id: str | None = None
    email: str | None = None


class ContactSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class SearchContactsOutput(_Base):
    contacts: list[ContactSummary] = Field(default_factory=list)
    count: int = 0
    contact_count: int = 0


class CreateContactListOutput(_Base):
    id: str | None = None
    name: str | None = None
    contact_count: int = 0


class ListSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    name: str | None = None
    contact_count: int = 0


class GetContactListsOutput(_Base):
    lists: list[ListSummary] = Field(default_factory=list)
    count: int = 0


class RemoveContactFromListOutput(_Base):
    message: str | None = None
    list_id: str | None = None
    contacts_removed: int = 0


class DeleteContactsOutput(_Base):
    message: str | None = None
    job_id: str | None = None
    deleted_count: int | str | None = None


class AddEmailToGlobalSuppressionOutput(_Base):
    message: str | None = None
    suppressed_emails: list[str] = Field(default_factory=list)


class DeleteGlobalSuppressionOutput(_Base):
    message: str | None = None
    email: str | None = None


class SuppressionRow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str | None = None
    created: int | None = None
    reason: str | None = None
    status: str | None = None


class ListGlobalSuppressionsOutput(_Base):
    suppressions: list[SuppressionRow] = Field(default_factory=list)
    count: int = 0


class GetAllBouncesOutput(_Base):
    bounces: list[SuppressionRow] = Field(default_factory=list)
    count: int = 0


class DeleteBouncesOutput(_Base):
    message: str | None = None
    deleted_count: int | str | None = None


class ListBlocksOutput(_Base):
    blocks: list[SuppressionRow] = Field(default_factory=list)
    count: int = 0


class DeleteBlocksOutput(_Base):
    message: str | None = None
    deleted_count: int | str | None = None


_LEGACY_FIELD_HINT: dict[str, Any] = {}  # placeholder for downstream type-checkers
