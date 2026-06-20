"""Pydantic response models for the Loops integration's @tool functions.

Loops follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it by reading the API key from the resolved ``api_key``
credential.

Error model: the tools wrap every call in a try/except, returning the
typed output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. We preserve that defensive
behavior — non-2xx HTTP responses do *not* raise. Every output model
carries both shapes.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Contact",
    "ContactProperty",
    "CreateContactOutput",
    "CreateContactPropertyOutput",
    "DeleteContactOutput",
    "FindContactOutput",
    "ListContactPropertiesOutput",
    "ListMailingListsOutput",
    "ListTransactionalEmailsOutput",
    "MailingList",
    "Pagination",
    "SendEventOutput",
    "SendTransactionalEmailOutput",
    "TransactionalEmail",
    "UpdateContactOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Contact(_Base):
    """A single contact row in ``find_contact``."""

    id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    source: str | None = None
    subscribed: bool | None = None
    user_group: str | None = None
    user_id: str | None = None
    mailing_lists: dict[str, Any] = Field(default_factory=dict)
    opt_in_status: str | None = None


class MailingList(_Base):
    """A single mailing list row in ``list_mailing_lists``."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    is_public: bool | None = None


class TransactionalEmail(_Base):
    """A single template row in ``list_transactional_emails``."""

    id: str | None = None
    name: str | None = None
    last_updated: str | None = None
    data_variables: list[str] = Field(default_factory=list)


class Pagination(_Base):
    """Pagination block returned by ``list_transactional_emails``."""

    total_results: int | None = None
    returned_results: int | None = None
    per_page: int | None = None
    total_pages: int | None = None
    next_cursor: str | None = None
    next_page: str | None = None


class ContactProperty(_Base):
    """A single property row in ``list_contact_properties``."""

    key: str | None = None
    label: str | None = None
    type: str | None = None


# --- Per-action output models ----------------------------------------------


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class UpdateContactOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None


class FindContactOutput(_Base):
    success: bool
    error: str | None = None
    contacts: list[Contact] = Field(default_factory=list)


class DeleteContactOutput(_Base):
    success: bool
    error: str | None = None
    message: str | None = None


class SendTransactionalEmailOutput(_Base):
    success: bool
    error: str | None = None


class SendEventOutput(_Base):
    success: bool
    error: str | None = None


class ListMailingListsOutput(_Base):
    success: bool
    error: str | None = None
    mailing_lists: list[MailingList] = Field(default_factory=list)


class ListTransactionalEmailsOutput(_Base):
    success: bool
    error: str | None = None
    transactional_emails: list[TransactionalEmail] = Field(default_factory=list)
    pagination: Pagination | None = None


class CreateContactPropertyOutput(_Base):
    success: bool
    error: str | None = None


class ListContactPropertiesOutput(_Base):
    success: bool
    error: str | None = None
    properties: list[ContactProperty] = Field(default_factory=list)
