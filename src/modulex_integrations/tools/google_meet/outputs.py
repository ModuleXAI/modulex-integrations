"""Pydantic response models for the google_meet integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ColorIdOption",
    "ListColorIdOptionsOutput",
    "ScheduleMeetingOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -------------------------------------------------


class ColorIdOption(_Base):
    """One color option exposed by the Google Calendar /colors endpoint."""

    id: str | None = None
    background: str | None = None
    foreground: str | None = None


# --- Per-action output models ----------------------------------------------


class ScheduleMeetingOutput(_Base):
    success: bool
    error: str | None = None
    event_id: str | None = None
    html_link: str | None = None
    hangout_link: str | None = None
    meet_link: str | None = None
    status: str | None = None
    summary: str | None = None
    start: dict[str, Any] | None = None
    end: dict[str, Any] | None = None
    attendees: list[dict[str, Any]] = Field(default_factory=list)
    conference_data: dict[str, Any] | None = None
    event: dict[str, Any] | None = None


class ListColorIdOptionsOutput(_Base):
    success: bool
    error: str | None = None
    options: list[ColorIdOption] = Field(default_factory=list)
    count: int = 0
