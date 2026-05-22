"""Pydantic response models for the google_contacts integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ContactSummary",
    "CreateContactOutput",
    "DeleteContactOutput",
    "GetContactOutput",
    "ListContactsOutput",
    "ListDirectoryContactsOutput",
    "UpdateContactOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class ContactSummary(_Base):
    """A Google People `Person` resource, projected to the fields most tools read."""

    resource_name: str | None = None
    etag: str | None = None
    display_name: str | None = None
    given_name: str | None = None
    family_name: str | None = None
    middle_name: str | None = None
    email_addresses: list[str] = Field(default_factory=list)
    phone_numbers: list[str] = Field(default_factory=list)
    organizations: list[dict[str, Any]] = Field(default_factory=list)
    addresses: list[dict[str, Any]] = Field(default_factory=list)
    biographies: list[dict[str, Any]] = Field(default_factory=list)
    urls: list[dict[str, Any]] = Field(default_factory=list)
    birthdays: list[dict[str, Any]] = Field(default_factory=list)
    genders: list[dict[str, Any]] = Field(default_factory=list)
    raw: dict[str, Any] = Field(
        default_factory=dict,
        description="Untouched upstream Person object — all fields requested via personFields.",
    )


# --- Per-action output models ----------------------------------------------


class CreateContactOutput(_Base):
    success: bool
    contact: ContactSummary | None = None


class DeleteContactOutput(_Base):
    success: bool
    resource_name: str | None = None


class GetContactOutput(_Base):
    success: bool
    contact: ContactSummary | None = None


class ListContactsOutput(_Base):
    success: bool
    contacts: list[ContactSummary] = Field(default_factory=list)
    total: int = 0


class ListDirectoryContactsOutput(_Base):
    success: bool
    people: list[ContactSummary] = Field(default_factory=list)
    next_page_token: str | None = None
    next_sync_token: str | None = None
    total: int = 0


class UpdateContactOutput(_Base):
    success: bool
    contact: ContactSummary | None = None
