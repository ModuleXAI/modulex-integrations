"""Pydantic response models for the Resend integration's @tool functions.

Resend's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it by reading the API key from the resolved
``api_key`` credential.

Error model: non-2xx HTTP responses and timeouts are caught and surface
as ``success=False`` + ``error`` rather than raising. Every output model
carries both the success and failure shapes.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ContactItem",
    "CreateContactOutput",
    "DeleteContactOutput",
    "DomainItem",
    "EmailTag",
    "GetContactOutput",
    "GetEmailOutput",
    "ListContactsOutput",
    "ListDomainsOutput",
    "SendOutput",
    "UpdateContactOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class EmailTag(_Base):
    """A single tag name/value pair attached to an email."""

    name: str | None = None
    value: str | None = None


class ContactItem(_Base):
    """A single contact row in ``list_contacts``."""

    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: str | None = None
    unsubscribed: bool | None = None


class DomainItem(_Base):
    """A single domain row in ``list_domains``."""

    id: str | None = None
    name: str | None = None
    status: str | None = None
    region: str | None = None
    created_at: str | None = None


# --- Per-action output models ----------------------------------------------


class SendOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    to: str | None = None
    subject: str | None = None
    body: str | None = None


class GetEmailOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    sender: str | None = None
    to: list[str] = Field(default_factory=list)
    subject: str | None = None
    html: str | None = None
    text: str | None = None
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    reply_to: list[str] = Field(default_factory=list)
    last_event: str | None = None
    created_at: str | None = None
    scheduled_at: str | None = None
    tags: list[EmailTag] = Field(default_factory=list)


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class ListContactsOutput(_Base):
    success: bool
    error: str | None = None
    contacts: list[ContactItem] = Field(default_factory=list)
    has_more: bool | None = None


class GetContactOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    created_at: str | None = None
    unsubscribed: bool | None = None


class UpdateContactOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class DeleteContactOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    deleted: bool | None = None


class ListDomainsOutput(_Base):
    success: bool
    error: str | None = None
    domains: list[DomainItem] = Field(default_factory=list)
    has_more: bool | None = None
