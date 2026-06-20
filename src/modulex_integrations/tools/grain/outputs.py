"""Pydantic response models for the Grain integration's @tool functions.

Grain's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved credential.

Error model: the upstream API returns proper HTTP status codes; the
tools wrap every call in try/except so non-2xx responses and timeouts
surface as ``success=False`` + ``error`` rather than raising. Every
output model carries both shapes (``success`` + ``error``) and keeps
data fields permissive (``<type> | None``), since the upstream payload
is read defensively with ``.get()``.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateHookOutput",
    "DeleteHookOutput",
    "GetRecordingOutput",
    "GetTranscriptOutput",
    "Hook",
    "ListHooksOutput",
    "ListMeetingTypesOutput",
    "ListRecordingsOutput",
    "ListTeamsOutput",
    "ListViewsOutput",
    "MeetingType",
    "Recording",
    "Team",
    "TranscriptSection",
    "View",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class Team(_Base):
    """A team object."""

    id: str | None = None
    name: str | None = None


class MeetingType(_Base):
    """A meeting type object."""

    id: str | None = None
    name: str | None = None
    scope: str | None = None


class View(_Base):
    """A Grain view object."""

    id: str | None = None
    name: str | None = None
    type: str | None = None


class Recording(_Base):
    """A meeting recording object.

    Extra include-blocks (highlights, participants, ai_summary,
    calendar_event, hubspot, etc.) are returned verbatim as
    JSON-serializable values.
    """

    id: str | None = None
    title: str | None = None
    start_datetime: str | None = None
    end_datetime: str | None = None
    duration_ms: int | None = None
    media_type: str | None = None
    source: str | None = None
    url: str | None = None
    thumbnail_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    teams: list[dict[str, Any]] = Field(default_factory=list)
    meeting_type: dict[str, Any] | None = None
    highlights: list[dict[str, Any]] | None = None
    participants: list[dict[str, Any]] | None = None
    ai_summary: dict[str, Any] | None = None
    calendar_event: dict[str, Any] | None = None
    hubspot: dict[str, Any] | None = None
    private_notes: dict[str, Any] | None = None
    ai_template_sections: list[dict[str, Any]] | None = None


class TranscriptSection(_Base):
    """A single transcript section (speaker turn)."""

    participant_id: str | None = None
    speaker: str | None = None
    start: int | None = None
    end: int | None = None
    text: str | None = None


class Hook(_Base):
    """A webhook subscription object."""

    id: str | None = None
    enabled: bool | None = None
    version: int | None = None
    hook_url: str | None = None
    view_id: str | None = None
    actions: list[str] = Field(default_factory=list)
    inserted_at: str | None = None


# --- Per-action output models ----------------------------------------------


class ListRecordingsOutput(_Base):
    success: bool
    error: str | None = None
    recordings: list[Recording] = Field(default_factory=list)
    cursor: str | None = None


class GetRecordingOutput(_Base):
    success: bool
    error: str | None = None
    recording: Recording | None = None


class GetTranscriptOutput(_Base):
    success: bool
    error: str | None = None
    transcript: list[TranscriptSection] = Field(default_factory=list)


class ListViewsOutput(_Base):
    success: bool
    error: str | None = None
    views: list[View] = Field(default_factory=list)


class ListTeamsOutput(_Base):
    success: bool
    error: str | None = None
    teams: list[Team] = Field(default_factory=list)


class ListMeetingTypesOutput(_Base):
    success: bool
    error: str | None = None
    meeting_types: list[MeetingType] = Field(default_factory=list)


class CreateHookOutput(_Base):
    success: bool
    error: str | None = None
    hook: Hook | None = None


class ListHooksOutput(_Base):
    success: bool
    error: str | None = None
    hooks: list[Hook] = Field(default_factory=list)


class DeleteHookOutput(_Base):
    success: bool
    error: str | None = None
