"""Pydantic response models for the sentry integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "EventSummary",
    "IssueSummary",
    "ListIssueEventsOutput",
    "ListProjectEventsOutput",
    "ListProjectIssuesOutput",
    "UpdateIssueOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class EventSummary(_Base):
    """A Sentry event object."""

    event_id: str | None = None
    title: str | None = None
    message: str | None = None
    platform: str | None = None
    date_created: str | None = None
    date_received: str | None = None
    tags: list[dict[str, str | None]] = Field(default_factory=list)


class IssueSummary(_Base):
    """A Sentry issue object."""

    id: str | None = None
    title: str | None = None
    short_id: str | None = None
    status: str | None = None
    level: str | None = None
    permalink: str | None = None
    assigned_to: str | None = None
    has_seen: bool | None = None
    is_bookmarked: bool | None = None
    is_public: bool | None = None
    count: str | None = None
    first_seen: str | None = None
    last_seen: str | None = None


# --- Per-action output models ---------------------------------------------


class ListIssueEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[EventSummary] = Field(default_factory=list)


class ListProjectEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[EventSummary] = Field(default_factory=list)


class ListProjectIssuesOutput(_Base):
    success: bool
    error: str | None = None
    issues: list[IssueSummary] = Field(default_factory=list)


class UpdateIssueOutput(_Base):
    success: bool
    error: str | None = None
    issue: IssueSummary | None = None
