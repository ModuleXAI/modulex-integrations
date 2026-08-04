"""Pydantic response models for the Fathom integration's @tool functions.

Fathom follows the modulex *api_key* runtime convention: each function
signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the runtime injects it from the
resolved credential. The key travels in the ``X-Api-Key`` header.

Error model: non-2xx HTTP responses, timeouts, and unexpected
exceptions are caught and returned as ``success=False`` + ``error``
rather than raising, so every model carries both shapes. Data fields
are permissive (``| None`` scalars, list defaults) because the API
omits optional blocks entirely unless the matching ``include_*`` flag
was requested.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "ActionItem",
    "ActionItemAssignee",
    "CalendarInvitee",
    "CrmCompanyMatch",
    "CrmContactMatch",
    "CrmDealMatch",
    "CrmMatches",
    "GetSummaryOutput",
    "GetTranscriptOutput",
    "Highlight",
    "ListMeetingTypesOutput",
    "ListMeetingsOutput",
    "ListTeamMembersOutput",
    "ListTeamsOutput",
    "Meeting",
    "MeetingSummary",
    "MeetingType",
    "Recorder",
    "Team",
    "TeamMember",
    "TranscriptEntry",
    "TranscriptSpeaker",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class TranscriptSpeaker(_Base):
    """Who said a transcript line."""

    display_name: str | None = None
    matched_calendar_invitee_email: str | None = None


class TranscriptEntry(_Base):
    """One utterance in a meeting transcript."""

    speaker: TranscriptSpeaker | None = None
    text: str | None = None
    timestamp: str | None = None


class MeetingSummary(_Base):
    """The AI-generated recap attached to a recording."""

    template_name: str | None = None
    markdown_formatted: str | None = None


class Recorder(_Base):
    """The user whose Fathom account captured the meeting."""

    name: str | None = None
    email: str | None = None
    email_domain: str | None = None
    team: str | None = None


class CalendarInvitee(_Base):
    """A person on the meeting's calendar event."""

    name: str | None = None
    email: str | None = None
    email_domain: str | None = None
    is_external: bool | None = None
    matched_speaker_display_name: str | None = None


class ActionItemAssignee(_Base):
    """Who owns an action item."""

    name: str | None = None
    email: str | None = None
    team: str | None = None


class ActionItem(_Base):
    """A commitment or next step extracted from the meeting."""

    description: str | None = None
    user_generated: bool | None = None
    completed: bool | None = None
    recording_timestamp: str | None = None
    recording_playback_url: str | None = None
    assignee: ActionItemAssignee | None = None


class Highlight(_Base):
    """A bookmarked moment in the recording."""

    type: str | None = None
    summary: str | None = None
    text: str | None = None
    start_time: float | None = None
    end_time: float | None = None


class CrmContactMatch(_Base):
    """A CRM contact linked to the meeting."""

    name: str | None = None
    email: str | None = None
    record_url: str | None = None


class CrmCompanyMatch(_Base):
    """A CRM company linked to the meeting."""

    name: str | None = None
    record_url: str | None = None


class CrmDealMatch(_Base):
    """A CRM deal linked to the meeting."""

    name: str | None = None
    amount: float | None = None
    record_url: str | None = None


class CrmMatches(_Base):
    """Contacts, companies, and deals matched from the linked CRM.

    ``error`` is populated when no CRM is connected for the workspace.
    """

    contacts: list[CrmContactMatch] = Field(default_factory=list)
    companies: list[CrmCompanyMatch] = Field(default_factory=list)
    deals: list[CrmDealMatch] = Field(default_factory=list)
    error: str | None = None


class Meeting(_Base):
    """A single recorded meeting.

    ``transcript``, ``action_items``, ``highlights``, ``default_summary``
    and ``crm_matches`` stay ``None`` unless the matching ``include_*``
    flag was set on the request.
    """

    title: str | None = None
    meeting_title: str | None = None
    meeting_type: str | None = None
    recording_id: int | None = None
    url: str | None = None
    meeting_url: str | None = None
    share_url: str | None = None
    created_at: str | None = None
    scheduled_start_time: str | None = None
    scheduled_end_time: str | None = None
    recording_start_time: str | None = None
    recording_end_time: str | None = None
    transcript_language: str | None = None
    calendar_invitees_domains_type: str | None = None
    shared_with: str | None = None
    recorded_by: Recorder | None = None
    calendar_invitees: list[CalendarInvitee] = Field(default_factory=list)
    default_summary: MeetingSummary | None = None
    transcript: list[TranscriptEntry] | None = None
    action_items: list[ActionItem] | None = None
    highlights: list[Highlight] | None = None
    crm_matches: CrmMatches | None = None


class MeetingType(_Base):
    """A meeting-type label configured for the organization."""

    name: str | None = None
    status: str | None = None
    created_at: str | None = None


class Team(_Base):
    """A team inside the organization."""

    name: str | None = None
    created_at: str | None = None


class TeamMember(_Base):
    """A member of the organization."""

    name: str | None = None
    email: str | None = None
    created_at: str | None = None


# --- Per-action output models ----------------------------------------------


class ListMeetingsOutput(_Base):
    """Return shape of ``list_meetings``."""

    success: bool
    error: str | None = None
    meetings: list[Meeting] = Field(default_factory=list)
    next_cursor: str | None = None
    limit: int | None = None


class ListMeetingTypesOutput(_Base):
    """Return shape of ``list_meeting_types``."""

    success: bool
    error: str | None = None
    meeting_types: list[MeetingType] = Field(default_factory=list)
    next_cursor: str | None = None
    limit: int | None = None


class GetSummaryOutput(_Base):
    """Return shape of ``get_summary``."""

    success: bool
    error: str | None = None
    template_name: str | None = None
    markdown_formatted: str | None = None


class GetTranscriptOutput(_Base):
    """Return shape of ``get_transcript``."""

    success: bool
    error: str | None = None
    transcript: list[TranscriptEntry] = Field(default_factory=list)


class ListTeamMembersOutput(_Base):
    """Return shape of ``list_team_members``."""

    success: bool
    error: str | None = None
    members: list[TeamMember] = Field(default_factory=list)
    next_cursor: str | None = None
    limit: int | None = None


class ListTeamsOutput(_Base):
    """Return shape of ``list_teams``."""

    success: bool
    error: str | None = None
    teams: list[Team] = Field(default_factory=list)
    next_cursor: str | None = None
    limit: int | None = None
