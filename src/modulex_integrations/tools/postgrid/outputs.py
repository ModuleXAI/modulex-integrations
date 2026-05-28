"""Pydantic response models for the postgrid integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "ContactResource",
    "CreateContactOutput",
    "CreateLetterOutput",
    "CreatePostcardOutput",
    "LetterResource",
    "PostcardResource",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class ContactResource(_Base):
    """A contact object returned by the PostGrid API."""

    id: str | None = None
    object: str | None = None
    live: bool | None = None
    first_name: str | None = None
    last_name: str | None = None
    company_name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    province_or_state: str | None = None
    postal_or_zip: str | None = None
    country: str | None = None
    country_code: str | None = None
    email: str | None = None
    phone_number: str | None = None
    job_title: str | None = None
    description: str | None = None
    address_status: str | None = None


class LetterResource(_Base):
    """A letter object returned by the PostGrid API."""

    id: str | None = None
    object: str | None = None
    live: bool | None = None
    send_date: str | None = None
    status: str | None = None
    url: str | None = None


class PostcardResource(_Base):
    """A postcard object returned by the PostGrid API."""

    id: str | None = None
    object: str | None = None
    live: bool | None = None
    send_date: str | None = None
    status: str | None = None
    size: str | None = None
    url: str | None = None


# --- Per-action output models ---------------------------------------------


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    contact: ContactResource | None = None


class CreateLetterOutput(_Base):
    success: bool
    error: str | None = None
    letter: LetterResource | None = None


class CreatePostcardOutput(_Base):
    success: bool
    error: str | None = None
    postcard: PostcardResource | None = None
