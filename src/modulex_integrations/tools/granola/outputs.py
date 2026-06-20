"""Pydantic response models for the Granola integration's @tool functions.

Granola's tools follow the modulex *api_key* runtime convention: each
function signature takes ``api_key: str`` directly, and the modulex
``ToolExecutor`` injects it from the resolved credential.

Error model: the API returns proper HTTP status codes; the tools wrap
every call in try/except so non-2xx responses and timeouts surface as
``success=False`` + ``error`` rather than raising. Every output model
carries both shapes — the success fields keep their pydantic defaults
on a failure branch.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Attendee",
    "FolderRef",
    "GetNoteOutput",
    "ListFoldersOutput",
    "ListNotesOutput",
    "NoteSummary",
    "TranscriptSegment",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class NoteSummary(_Base):
    """A single note row in ``list_notes``."""

    id: str | None = None
    title: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class Attendee(_Base):
    """A meeting attendee in ``get_note``."""

    name: str | None = None
    email: str | None = None


class FolderRef(_Base):
    """A folder reference.

    Used both for a note's folder memberships in ``get_note`` (id, name)
    and for the workspace folder listing in ``list_folders``
    (id, name, parent_folder_id).
    """

    id: str | None = None
    name: str | None = None
    parent_folder_id: str | None = None


class TranscriptSegment(_Base):
    """A single transcript entry in ``get_note``."""

    speaker: str | None = None
    speaker_label: str | None = None
    text: str | None = None
    start_time: str | None = None
    end_time: str | None = None


# --- Per-action output models ----------------------------------------------


class ListNotesOutput(_Base):
    success: bool
    error: str | None = None
    notes: list[NoteSummary] = Field(default_factory=list)
    has_more: bool = False
    cursor: str | None = None


class GetNoteOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    title: str | None = None
    owner_name: str | None = None
    owner_email: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    web_url: str | None = None
    summary_text: str | None = None
    summary_markdown: str | None = None
    attendees: list[Attendee] = Field(default_factory=list)
    folders: list[FolderRef] = Field(default_factory=list)
    calendar_event_title: str | None = None
    calendar_organiser: str | None = None
    calendar_event_id: str | None = None
    scheduled_start_time: str | None = None
    scheduled_end_time: str | None = None
    invitees: list[str] = Field(default_factory=list)
    transcript: list[TranscriptSegment] | None = None


class ListFoldersOutput(_Base):
    success: bool
    error: str | None = None
    folders: list[FolderRef] = Field(default_factory=list)
    has_more: bool = False
    cursor: str | None = None
