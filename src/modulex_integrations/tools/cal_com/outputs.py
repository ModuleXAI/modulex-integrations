"""Pydantic response models for the cal_com integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BookingItem",
    "CreateBookingOutput",
    "DeleteBookingOutput",
    "EventTypeOption",
    "GetAllBookingsOutput",
    "GetBookableSlot",
    "GetBookableSlotsOutput",
    "GetBookingOutput",
    "ListEventTypeIdOptionsOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class BookingItem(_Base):
    """A booking object returned by the Cal.com API."""

    uid: str | None = None
    title: str | None = None
    status: str | None = None
    start: str | None = None
    end: str | None = None
    attendees: list[dict[str, Any]] = Field(default_factory=list)
    hosts: list[dict[str, Any]] = Field(default_factory=list)
    event_type_id: int | None = None
    meeting_url: str | None = None
    location: str | None = None


class GetBookableSlot(_Base):
    """A single available time slot."""

    time: str | None = None
    start: str | None = None
    end: str | None = None


class EventTypeOption(_Base):
    """An event type with its ID and title."""

    label: str | None = None
    value: int | None = None


# --- Per-action output models ----------------------------------------------


class CreateBookingOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None
    booking: BookingItem | None = None


class DeleteBookingOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None


class GetAllBookingsOutput(_Base):
    success: bool
    error: str | None = None
    bookings: list[BookingItem] = Field(default_factory=list)
    total: int = 0


class GetBookableSlotsOutput(_Base):
    success: bool
    error: str | None = None
    slots: dict[str, list[GetBookableSlot]] = Field(default_factory=dict)


class GetBookingOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None
    booking: BookingItem | None = None


class ListEventTypeIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    event_types: list[EventTypeOption] = Field(default_factory=list)
