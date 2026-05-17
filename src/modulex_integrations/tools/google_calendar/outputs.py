"""Pydantic response models for the google_calendar integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddAttendeesToEventOutput",
    "CalendarSummary",
    "ColorEntry",
    "CreateEventOutput",
    "DeleteEventOutput",
    "EventSummary",
    "FreeBusyCalendar",
    "FreeBusyPeriod",
    "GetCalendarOutput",
    "GetCurrentUserOutput",
    "GetDateTimeOutput",
    "GetEventOutput",
    "ListCalendarsOutput",
    "ListColorIdOptionsOutput",
    "ListEventInstancesOutput",
    "ListEventsOutput",
    "QueryFreeBusyCalendarsOutput",
    "QuickAddEventOutput",
    "SettingItem",
    "UpdateEventInstanceOutput",
    "UpdateEventOutput",
    "UpdateFollowingInstancesOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -------------------------------------------------


class CalendarSummary(_Base):
    id: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    timeZone: str | None = None
    kind: str | None = None
    etag: str | None = None
    accessRole: str | None = None
    primary: bool | None = None
    selected: bool | None = None
    backgroundColor: str | None = None
    foregroundColor: str | None = None
    colorId: str | None = None
    hidden: bool | None = None


class EventSummary(_Base):
    id: str | None = None
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    status: str | None = None
    htmlLink: str | None = None
    created: str | None = None
    updated: str | None = None
    start: dict[str, Any] | None = None
    end: dict[str, Any] | None = None
    creator: dict[str, Any] | None = None
    organizer: dict[str, Any] | None = None
    attendees: list[dict[str, Any]] = Field(default_factory=list)
    recurrence: list[str] | None = None
    recurringEventId: str | None = None
    visibility: str | None = None
    colorId: str | None = None
    conferenceData: dict[str, Any] | None = None
    hangoutLink: str | None = None
    kind: str | None = None
    etag: str | None = None
    iCalUID: str | None = None
    sequence: int | None = None
    eventType: str | None = None


class ColorEntry(_Base):
    label: str | None = None
    value: str | None = None


class SettingItem(_Base):
    id: str | None = None
    value: Any | None = None
    kind: str | None = None
    etag: str | None = None


class FreeBusyPeriod(_Base):
    start: str | None = None
    end: str | None = None


class FreeBusyCalendar(_Base):
    busy: list[FreeBusyPeriod] = Field(default_factory=list)
    errors: list[dict[str, Any]] | None = None


# --- Per-action output models -----------------------------------------------


class AddAttendeesToEventOutput(_Base):
    success: bool
    event: EventSummary | None = None


class CreateEventOutput(_Base):
    success: bool
    event: EventSummary | None = None


class DeleteEventOutput(_Base):
    success: bool
    eventId: str | None = None
    statusCode: int | None = None


class GetCalendarOutput(_Base):
    success: bool
    calendar: CalendarSummary | None = None


class GetCurrentUserOutput(_Base):
    success: bool
    primaryCalendar: CalendarSummary | None = None
    calendars: list[CalendarSummary] = Field(default_factory=list)
    settings: list[SettingItem] = Field(default_factory=list)
    timezone: str | None = None
    locale: str | None = None
    colors: dict[str, Any] | None = None


class GetDateTimeOutput(_Base):
    success: bool
    date: str | None = None
    time: str | None = None
    timezone: str | None = None
    timezoneOffset: str | None = None
    timestamp: int | None = None
    isoString: str | None = None
    rfc3339: str | None = None


class GetEventOutput(_Base):
    success: bool
    event: EventSummary | None = None


class ListCalendarsOutput(_Base):
    success: bool
    calendars: list[CalendarSummary] = Field(default_factory=list)


class ListColorIdOptionsOutput(_Base):
    success: bool
    options: list[ColorEntry] = Field(default_factory=list)


class ListEventInstancesOutput(_Base):
    success: bool
    instances: list[EventSummary] = Field(default_factory=list)


class ListEventsOutput(_Base):
    success: bool
    events: list[EventSummary] = Field(default_factory=list)


class QueryFreeBusyCalendarsOutput(_Base):
    success: bool
    timeMin: str | None = None
    timeMax: str | None = None
    calendars: dict[str, FreeBusyCalendar] = Field(default_factory=dict)


class QuickAddEventOutput(_Base):
    success: bool
    event: EventSummary | None = None


class UpdateEventOutput(_Base):
    success: bool
    event: EventSummary | None = None


class UpdateEventInstanceOutput(_Base):
    success: bool
    event: EventSummary | None = None


class UpdateFollowingInstancesOutput(_Base):
    success: bool
    originalEventId: str | None = None
    newEvent: EventSummary | None = None
    trimmedRecurrence: list[str] | None = None
