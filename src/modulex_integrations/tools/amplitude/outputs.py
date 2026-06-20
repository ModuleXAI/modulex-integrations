"""Pydantic response models for the amplitude integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "EventSegmentationOutput",
    "GetActiveUsersOutput",
    "GetRevenueOutput",
    "GroupIdentifyOutput",
    "IdentifyUserOutput",
    "ListEventsOutput",
    "ProjectEvent",
    "RealtimeActiveUsersOutput",
    "SendEventOutput",
    "UserActivityEvent",
    "UserActivityOutput",
    "UserData",
    "UserProfileOutput",
    "UserSearchMatch",
    "UserSearchOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class UserSearchMatch(_Base):
    """A single user-search match entry."""

    amplitude_id: int | None = None
    user_id: str | None = None


class UserActivityEvent(_Base):
    """A single event in a user's activity stream."""

    event_type: str | None = None
    event_time: str | None = None
    event_properties: dict[str, Any] = Field(default_factory=dict)
    user_properties: dict[str, Any] = Field(default_factory=dict)
    session_id: int | None = None
    platform: str | None = None
    country: str | None = None
    city: str | None = None


class UserData(_Base):
    """User metadata returned alongside an activity stream."""

    user_id: str | None = None
    canonical_amplitude_id: int | None = None
    num_events: int | None = None
    num_sessions: int | None = None
    platform: str | None = None
    country: str | None = None


class ProjectEvent(_Base):
    """A single event type listed for the project."""

    value: str | None = None
    display_name: str | None = None
    totals: int | None = None
    hidden: bool | None = None
    deleted: bool | None = None


# --- Per-action output models ---------------------------------------------


class SendEventOutput(_Base):
    success: bool
    error: str | None = None
    code: int | None = None
    events_ingested: int | None = None
    payload_size_bytes: int | None = None
    server_upload_time: int | None = None


class IdentifyUserOutput(_Base):
    success: bool
    error: str | None = None
    code: int | None = None
    message: str | None = None


class GroupIdentifyOutput(_Base):
    success: bool
    error: str | None = None
    code: int | None = None
    message: str | None = None


class UserSearchOutput(_Base):
    success: bool
    error: str | None = None
    matches: list[UserSearchMatch] = Field(default_factory=list)
    type: str | None = None


class UserActivityOutput(_Base):
    success: bool
    error: str | None = None
    events: list[UserActivityEvent] = Field(default_factory=list)
    user_data: UserData | None = None


class UserProfileOutput(_Base):
    success: bool
    error: str | None = None
    user_id: str | None = None
    device_id: str | None = None
    amp_props: dict[str, Any] | None = None
    cohort_ids: list[str] | None = None
    computations: dict[str, Any] | None = None


class EventSegmentationOutput(_Base):
    success: bool
    error: str | None = None
    series: list[Any] = Field(default_factory=list)
    series_labels: list[Any] = Field(default_factory=list)
    series_collapsed: list[Any] = Field(default_factory=list)
    x_values: list[str] = Field(default_factory=list)


class GetActiveUsersOutput(_Base):
    success: bool
    error: str | None = None
    series: list[Any] = Field(default_factory=list)
    series_meta: list[str] = Field(default_factory=list)
    x_values: list[str] = Field(default_factory=list)


class RealtimeActiveUsersOutput(_Base):
    success: bool
    error: str | None = None
    series: list[Any] = Field(default_factory=list)
    series_labels: list[str] = Field(default_factory=list)
    x_values: list[str] = Field(default_factory=list)


class ListEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[ProjectEvent] = Field(default_factory=list)


class GetRevenueOutput(_Base):
    success: bool
    error: str | None = None
    series: list[Any] = Field(default_factory=list)
    series_labels: list[str] = Field(default_factory=list)
    x_values: list[str] = Field(default_factory=list)
