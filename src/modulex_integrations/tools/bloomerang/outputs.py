"""Pydantic response models for the bloomerang integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

__all__ = [
    "AddInteractionOutput",
    "CreateConstituentOutput",
    "CreateDonationOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateConstituentOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    full_name: str | None = None
    type: str | None = None


class CreateDonationOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    amount: float | None = None
    date: str | None = None


class AddInteractionOutput(_Base):
    success: bool
    error: str | None = None
    id: int | None = None
    subject: str | None = None
    channel: str | None = None
