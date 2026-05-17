"""Pydantic response models for the microsoft_outlook integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddLabelToEmailOutput",
    "ApproveWorkflowOutput",
    "ContactSummary",
    "CreateContactOutput",
    "CreateDraftEmailOutput",
    "CreateDraftReplyOutput",
    "DownloadAttachmentOutput",
    "FindContactsOutput",
    "FindEmailOutput",
    "FindSharedFolderEmailOutput",
    "FolderSummary",
    "GetCurrentUserOutput",
    "GetMessageOutput",
    "ImportantMailItem",
    "LabelSummary",
    "ListContactsOutput",
    "ListFoldersOutput",
    "ListImportantMailOutput",
    "ListLabelsOutput",
    "MessageSummary",
    "MoveEmailToFolderOutput",
    "RemoveLabelFromEmailOutput",
    "ReplyToEmailOutput",
    "SendEmailOutput",
    "UpdateContactOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class ContactSummary(_Base):
    id: str | None = None
    displayName: str | None = None
    givenName: str | None = None
    surname: str | None = None
    emailAddresses: list[dict[str, Any]] = Field(default_factory=list)
    businessPhones: list[str] = Field(default_factory=list)


class MessageSummary(_Base):
    id: str | None = None
    subject: str | None = None
    isDraft: bool | None = None
    webLink: str | None = None
    from_: dict[str, Any] | None = Field(default=None, alias="from")
    sender: dict[str, Any] | None = None
    toRecipients: list[dict[str, Any]] = Field(default_factory=list)
    ccRecipients: list[dict[str, Any]] = Field(default_factory=list)
    bccRecipients: list[dict[str, Any]] = Field(default_factory=list)
    body: dict[str, Any] | None = None
    bodyPreview: str | None = None
    receivedDateTime: str | None = None
    categories: list[str] = Field(default_factory=list)
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    parentFolderId: str | None = None


class FolderSummary(_Base):
    id: str | None = None
    displayName: str | None = None
    parentFolderId: str | None = None
    totalItemCount: int | None = None
    unreadItemCount: int | None = None


class LabelSummary(_Base):
    id: str | None = None
    displayName: str | None = None
    color: str | None = None


class ImportantMailItem(_Base):
    id: str | None = None
    subject: str | None = None
    sender: str | None = None
    receivedDateTime: str | None = None


# --- Per-action output models ----------------------------------------------


class AddLabelToEmailOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    subject: str | None = None
    categories: list[str] = Field(default_factory=list)


class ApproveWorkflowOutput(_Base):
    success: bool
    error: str | None = None
    sent: bool | None = None


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    contact: ContactSummary | None = None


class CreateDraftEmailOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    subject: str | None = None
    isDraft: bool | None = None
    webLink: str | None = None


class CreateDraftReplyOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    subject: str | None = None
    isDraft: bool | None = None


class DownloadAttachmentOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    content_type: str | None = None
    size: int | None = None
    content_bytes_base64: str | None = None


class FindContactsOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    contacts: list[dict[str, Any]] = Field(default_factory=list)


class FindEmailOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    messages: list[dict[str, Any]] = Field(default_factory=list)


class FindSharedFolderEmailOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    messages: list[dict[str, Any]] = Field(default_factory=list)


class GetCurrentUserOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    displayName: str | None = None
    mail: str | None = None
    userPrincipalName: str | None = None


class GetMessageOutput(_Base):
    success: bool
    error: str | None = None
    message: dict[str, Any] | None = None


class ListContactsOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    contacts: list[dict[str, Any]] = Field(default_factory=list)


class ListFoldersOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    folders: list[dict[str, Any]] = Field(default_factory=list)


class ListImportantMailOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    data: list[ImportantMailItem] = Field(default_factory=list)


class ListLabelsOutput(_Base):
    success: bool
    error: str | None = None
    count: int = 0
    labels: list[dict[str, Any]] = Field(default_factory=list)


class MoveEmailToFolderOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    parentFolderId: str | None = None


class RemoveLabelFromEmailOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    categories: list[str] = Field(default_factory=list)


class ReplyToEmailOutput(_Base):
    success: bool
    error: str | None = None
    sent: bool | None = None


class SendEmailOutput(_Base):
    success: bool
    error: str | None = None
    sent: bool | None = None


class UpdateContactOutput(_Base):
    success: bool
    error: str | None = None
    contact: ContactSummary | None = None
