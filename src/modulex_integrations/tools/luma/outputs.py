"""Pydantic response models for the luma integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddGuestsOutput",
    "CreateEventOutput",
    "GetEventOutput",
    "GetGuestOutput",
    "GetGuestsOutput",
    "ListEventsOutput",
    "ListTicketTypesOutput",
    "SendInvitesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateEventOutput(_Base):
    success: bool
    error: str | None = None
    event: dict[str, Any] | None = None


class GetEventOutput(_Base):
    success: bool
    error: str | None = None
    event: dict[str, Any] | None = None


class ListEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[dict[str, Any]] = Field(default_factory=list)
    has_more: bool | None = None
    next_cursor: str | None = None


class GetGuestOutput(_Base):
    success: bool
    error: str | None = None
    guest: dict[str, Any] | None = None


class GetGuestsOutput(_Base):
    success: bool
    error: str | None = None
    guests: list[dict[str, Any]] = Field(default_factory=list)
    has_more: bool | None = None
    next_cursor: str | None = None


class AddGuestsOutput(_Base):
    success: bool
    error: str | None = None
    guests: list[dict[str, Any]] = Field(default_factory=list)


class ListTicketTypesOutput(_Base):
    success: bool
    error: str | None = None
    ticket_types: list[dict[str, Any]] = Field(default_factory=list)


class SendInvitesOutput(_Base):
    success: bool
    error: str | None = None
