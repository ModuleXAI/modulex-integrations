"""Pydantic response models for the insightly integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "CreateContactOutput",
    "CreateTaskOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    contact_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    email_address: str | None = None
    title: str | None = None
    phone: str | None = None


class CreateTaskOutput(_Base):
    success: bool
    error: str | None = None
    task_id: int | None = None
    title: str | None = None
    status: str | None = None
    due_date: str | None = None
    category_id: int | None = None
