"""Pydantic response models for the microsoft_365_people integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ContactFolderOutput",
    "ContactOutput",
    "CreateContactFolderOutput",
    "CreateContactOutput",
    "EmailAddress",
    "HomeAddress",
    "UpdateContactOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class EmailAddress(_Base):
    """An email address entry on a contact."""

    name: str | None = None
    address: str | None = None


class HomeAddress(_Base):
    """A physical address on a contact."""

    street: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country_or_region: str | None = None


class ContactOutput(_Base):
    """A Microsoft 365 contact resource."""

    id: str | None = None
    display_name: str | None = None
    given_name: str | None = None
    surname: str | None = None
    email_addresses: list[EmailAddress] = Field(default_factory=list)
    mobile_phone: str | None = None
    home_phones: list[str] = Field(default_factory=list)
    home_address: HomeAddress | None = None
    created_date_time: str | None = None
    last_modified_date_time: str | None = None


class ContactFolderOutput(_Base):
    """A Microsoft 365 contact folder resource."""

    id: str | None = None
    display_name: str | None = None
    parent_folder_id: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateContactOutput(_Base):
    success: bool
    contact: ContactOutput | None = None


class CreateContactFolderOutput(_Base):
    success: bool
    folder: ContactFolderOutput | None = None


class UpdateContactOutput(_Base):
    success: bool
    contact: ContactOutput | None = None
