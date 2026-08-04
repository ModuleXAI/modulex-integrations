"""Fathom LangChain ``@tool`` functions.

Six async tools wrapping the Fathom External API
(``https://api.fathom.ai/external/v1``). The calling convention is the
modulex *api_key* one: the runtime injects an ``api_key: str`` directly
(resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair. The key is sent in the ``X-Api-Key``
header on every request.

The host is a single compile-time constant — no action parameter ever
reaches the netloc, and the one path parameter (``recording_id``) is
percent-encoded before it is interpolated.

Error model: non-2xx HTTP responses, timeouts, and unexpected
exceptions do *not* raise — they are returned as the typed output with
``success=False`` + ``error``. Error bodies are unwrapped from
``message``/``error`` when present, otherwise the status and raw body
are reported. Success payloads are parsed defensively: a 200 whose body
is not the documented object shape degrades to empty values instead of
blowing up past the ``@tool`` boundary.

Pagination is cursor-based and explicit: every list action accepts a
``cursor`` and returns ``next_cursor``. No action loops internally, so
one invocation is always exactly one upstream request.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.fathom.outputs import (
    ActionItem,
    ActionItemAssignee,
    CalendarInvitee,
    CrmCompanyMatch,
    CrmContactMatch,
    CrmDealMatch,
    CrmMatches,
    GetSummaryOutput,
    GetTranscriptOutput,
    Highlight,
    ListMeetingsOutput,
    ListMeetingTypesOutput,
    ListTeamMembersOutput,
    ListTeamsOutput,
    Meeting,
    MeetingSummary,
    MeetingType,
    Recorder,
    Team,
    TeamMember,
    TranscriptEntry,
    TranscriptSpeaker,
)

__all__ = [
    "get_summary",
    "get_transcript",
    "list_meeting_types",
    "list_meetings",
    "list_team_members",
    "list_teams",
]

_FATHOM_API_BASE = "https://api.fathom.ai/external/v1"
_TIMEOUT = 30.0
# Transcripts and meeting listings that embed transcripts are the heavy
# endpoints (Fathom throttles them separately), so they get more headroom.
_LONG_TIMEOUT = 60.0

_EMPTY_KEY_ERROR = "Fathom API key is empty. Please configure a valid Fathom credential."

# Closed set from the API's own enum for the meetings invitee-domain filter.
_INVITEE_DOMAIN_TYPES = ("all", "only_internal", "one_or_more_external")


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Parse guards ----------------------------------------------------------


def _as_dict(payload: Any) -> dict[str, Any]:
    """A non-object 200 body degrades to empty rather than raising."""
    return payload if isinstance(payload, dict) else {}


def _dict_list(value: Any) -> list[dict[str, Any]]:
    """Keep only the object entries of a list-shaped payload."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_str(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _as_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip())
        except ValueError:
            return None
    return None


def _error(response: httpx.Response) -> str:
    """Build the error string for a non-2xx Fathom response."""
    try:
        body = _as_dict(response.json())
    except Exception:
        body = {}
    for key in ("message", "error"):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return f"Fathom API error ({response.status_code}): {value.strip()}"
    text = response.text.strip()
    detail = text or response.reason_phrase or "no response body"
    return f"Fathom API error ({response.status_code}): {detail}"


# --- Record parsers --------------------------------------------------------


def _parse_transcript(value: Any) -> list[TranscriptEntry]:
    entries: list[TranscriptEntry] = []
    for item in _dict_list(value):
        speaker = _as_dict(item.get("speaker"))
        entries.append(
            TranscriptEntry(
                speaker=TranscriptSpeaker(
                    display_name=_as_str(speaker.get("display_name")),
                    matched_calendar_invitee_email=_as_str(
                        speaker.get("matched_calendar_invitee_email")
                    ),
                ),
                text=_as_str(item.get("text")),
                timestamp=_as_str(item.get("timestamp")),
            )
        )
    return entries


def _parse_summary(record: dict[str, Any]) -> MeetingSummary:
    return MeetingSummary(
        template_name=_as_str(record.get("template_name")),
        markdown_formatted=_as_str(record.get("markdown_formatted")),
    )


def _parse_recorder(value: Any) -> Recorder | None:
    if not isinstance(value, dict):
        return None
    return Recorder(
        name=_as_str(value.get("name")),
        email=_as_str(value.get("email")),
        email_domain=_as_str(value.get("email_domain")),
        team=_as_str(value.get("team")),
    )


def _parse_invitees(value: Any) -> list[CalendarInvitee]:
    return [
        CalendarInvitee(
            name=_as_str(item.get("name")),
            email=_as_str(item.get("email")),
            email_domain=_as_str(item.get("email_domain")),
            is_external=_as_bool(item.get("is_external")),
            matched_speaker_display_name=_as_str(item.get("matched_speaker_display_name")),
        )
        for item in _dict_list(value)
    ]


def _parse_action_items(value: Any) -> list[ActionItem]:
    items: list[ActionItem] = []
    for item in _dict_list(value):
        assignee = _as_dict(item.get("assignee"))
        items.append(
            ActionItem(
                description=_as_str(item.get("description")),
                user_generated=_as_bool(item.get("user_generated")),
                completed=_as_bool(item.get("completed")),
                recording_timestamp=_as_str(item.get("recording_timestamp")),
                recording_playback_url=_as_str(item.get("recording_playback_url")),
                assignee=ActionItemAssignee(
                    name=_as_str(assignee.get("name")),
                    email=_as_str(assignee.get("email")),
                    team=_as_str(assignee.get("team")),
                ),
            )
        )
    return items


def _parse_highlights(value: Any) -> list[Highlight]:
    return [
        Highlight(
            type=_as_str(item.get("type")),
            summary=_as_str(item.get("summary")),
            text=_as_str(item.get("text")),
            start_time=_as_float(item.get("start_time")),
            end_time=_as_float(item.get("end_time")),
        )
        for item in _dict_list(value)
    ]


def _parse_crm_matches(value: Any) -> CrmMatches | None:
    if not isinstance(value, dict):
        return None
    return CrmMatches(
        contacts=[
            CrmContactMatch(
                name=_as_str(item.get("name")),
                email=_as_str(item.get("email")),
                record_url=_as_str(item.get("record_url")),
            )
            for item in _dict_list(value.get("contacts"))
        ],
        companies=[
            CrmCompanyMatch(
                name=_as_str(item.get("name")),
                record_url=_as_str(item.get("record_url")),
            )
            for item in _dict_list(value.get("companies"))
        ],
        deals=[
            CrmDealMatch(
                name=_as_str(item.get("name")),
                amount=_as_float(item.get("amount")),
                record_url=_as_str(item.get("record_url")),
            )
            for item in _dict_list(value.get("deals"))
        ],
        error=_as_str(value.get("error")),
    )


def _parse_meeting(record: dict[str, Any]) -> Meeting:
    raw_summary = record.get("default_summary")
    raw_transcript = record.get("transcript")
    raw_action_items = record.get("action_items")
    raw_highlights = record.get("highlights")
    return Meeting(
        title=_as_str(record.get("title")),
        meeting_title=_as_str(record.get("meeting_title")),
        meeting_type=_as_str(record.get("meeting_type")),
        recording_id=_as_int(record.get("recording_id")),
        url=_as_str(record.get("url")),
        meeting_url=_as_str(record.get("meeting_url")),
        share_url=_as_str(record.get("share_url")),
        created_at=_as_str(record.get("created_at")),
        scheduled_start_time=_as_str(record.get("scheduled_start_time")),
        scheduled_end_time=_as_str(record.get("scheduled_end_time")),
        recording_start_time=_as_str(record.get("recording_start_time")),
        recording_end_time=_as_str(record.get("recording_end_time")),
        transcript_language=_as_str(record.get("transcript_language")),
        calendar_invitees_domains_type=_as_str(record.get("calendar_invitees_domains_type")),
        shared_with=_as_str(record.get("shared_with")),
        recorded_by=_parse_recorder(record.get("recorded_by")),
        calendar_invitees=_parse_invitees(record.get("calendar_invitees")),
        default_summary=(
            _parse_summary(raw_summary) if isinstance(raw_summary, dict) else None
        ),
        transcript=(
            _parse_transcript(raw_transcript) if isinstance(raw_transcript, list) else None
        ),
        action_items=(
            _parse_action_items(raw_action_items)
            if isinstance(raw_action_items, list)
            else None
        ),
        highlights=(
            _parse_highlights(raw_highlights) if isinstance(raw_highlights, list) else None
        ),
        crm_matches=_parse_crm_matches(record.get("crm_matches")),
    )


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListMeetingsInput(BaseModel):
    api_key: str = Field(description="Fathom API key (provided by credential system)")
    include_summary: bool = Field(
        default=False, description="Include each meeting's summary in the response"
    )
    include_transcript: bool = Field(
        default=False, description="Include each meeting's full transcript in the response"
    )
    include_action_items: bool = Field(
        default=False, description="Include action items extracted from each meeting"
    )
    include_crm_matches: bool = Field(
        default=False,
        description="Include CRM matches (only returns data from a linked CRM)",
    )
    include_highlights: bool = Field(
        default=False, description="Include highlighted moments from each meeting"
    )
    created_after: str | None = Field(
        default=None,
        description="Only meetings created after this ISO 8601 timestamp "
        "(e.g. 2025-01-01T00:00:00Z)",
    )
    created_before: str | None = Field(
        default=None,
        description="Only meetings created before this ISO 8601 timestamp "
        "(e.g. 2025-12-31T23:59:59Z)",
    )
    recorded_by: str | None = Field(
        default=None, description="Filter by the email address of the user who recorded"
    )
    teams: str | None = Field(default=None, description="Filter by team name")
    meeting_type: str | None = Field(
        default=None, description="Filter by meeting type name (see list_meeting_types)"
    )
    calendar_invitees_domains: str | None = Field(
        default=None, description="Filter by calendar invitee company domain (exact match)"
    )
    calendar_invitees_domains_type: str | None = Field(
        default=None,
        description="Invitee domain filter: 'all', 'only_internal', or 'one_or_more_external'",
    )
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )


class ListMeetingTypesInput(BaseModel):
    api_key: str = Field(description="Fathom API key (provided by credential system)")
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )


class GetSummaryInput(BaseModel):
    recording_id: str = Field(description="The recording ID of the meeting (e.g. 123456789)")
    api_key: str = Field(description="Fathom API key (provided by credential system)")


class GetTranscriptInput(BaseModel):
    recording_id: str = Field(description="The recording ID of the meeting (e.g. 123456789)")
    api_key: str = Field(description="Fathom API key (provided by credential system)")


class ListTeamMembersInput(BaseModel):
    api_key: str = Field(description="Fathom API key (provided by credential system)")
    team: str | None = Field(default=None, description="Team name to filter by")
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )


class ListTeamsInput(BaseModel):
    api_key: str = Field(description="Fathom API key (provided by credential system)")
    cursor: str | None = Field(
        default=None, description="Pagination cursor from a previous response"
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListMeetingsInput)
@serialize_pydantic_return
async def list_meetings(
    api_key: str,
    include_summary: bool = False,
    include_transcript: bool = False,
    include_action_items: bool = False,
    include_crm_matches: bool = False,
    include_highlights: bool = False,
    created_after: str | None = None,
    created_before: str | None = None,
    recorded_by: str | None = None,
    teams: str | None = None,
    meeting_type: str | None = None,
    calendar_invitees_domains: str | None = None,
    calendar_invitees_domains_type: str | None = None,
    cursor: str | None = None,
) -> ListMeetingsOutput:
    """List recent meetings recorded by the user or shared to their team."""
    if not api_key or not api_key.strip():
        return ListMeetingsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if include_summary:
        params["include_summary"] = "true"
    if include_transcript:
        params["include_transcript"] = "true"
    if include_action_items:
        params["include_action_items"] = "true"
    if include_crm_matches:
        params["include_crm_matches"] = "true"
    if include_highlights:
        params["include_highlights"] = "true"
    if created_after:
        params["created_after"] = created_after.strip()
    if created_before:
        params["created_before"] = created_before.strip()
    if recorded_by:
        params["recorded_by[]"] = recorded_by.strip()
    if teams:
        params["teams[]"] = teams.strip()
    if meeting_type:
        params["meeting_type"] = meeting_type.strip()
    if calendar_invitees_domains:
        params["calendar_invitees_domains[]"] = calendar_invitees_domains.strip()
    if calendar_invitees_domains_type:
        domains_type = calendar_invitees_domains_type.strip().lower()
        if domains_type not in _INVITEE_DOMAIN_TYPES:
            return ListMeetingsOutput(
                success=False,
                error=(
                    "calendar_invitees_domains_type must be one of "
                    f"{', '.join(_INVITEE_DOMAIN_TYPES)}."
                ),
            )
        # 'all' is the API default; sending it adds nothing.
        if domains_type != "all":
            params["calendar_invitees_domains_type"] = domains_type
    if cursor:
        params["cursor"] = cursor.strip()

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.get(
                f"{_FATHOM_API_BASE}/meetings", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListMeetingsOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListMeetingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMeetingsOutput(success=False, error=f"List meetings failed: {exc}")

    return ListMeetingsOutput(
        success=True,
        meetings=[_parse_meeting(item) for item in _dict_list(data.get("items"))],
        next_cursor=_as_str(data.get("next_cursor")),
        limit=_as_int(data.get("limit")),
    )


@tool(args_schema=ListMeetingTypesInput)
@serialize_pydantic_return
async def list_meeting_types(
    api_key: str,
    cursor: str | None = None,
) -> ListMeetingTypesOutput:
    """List meeting types configured in your Fathom organization."""
    if not api_key or not api_key.strip():
        return ListMeetingTypesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if cursor:
        params["cursor"] = cursor.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_FATHOM_API_BASE}/meeting_types", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListMeetingTypesOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListMeetingTypesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMeetingTypesOutput(success=False, error=f"List meeting types failed: {exc}")

    return ListMeetingTypesOutput(
        success=True,
        meeting_types=[
            MeetingType(
                name=_as_str(item.get("name")),
                status=_as_str(item.get("status")),
                created_at=_as_str(item.get("created_at")),
            )
            for item in _dict_list(data.get("items"))
        ],
        next_cursor=_as_str(data.get("next_cursor")),
        limit=_as_int(data.get("limit")),
    )


@tool(args_schema=GetSummaryInput)
@serialize_pydantic_return
async def get_summary(recording_id: str, api_key: str) -> GetSummaryOutput:
    """Get the call summary for a specific meeting recording."""
    if not api_key or not api_key.strip():
        return GetSummaryOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not recording_id or not recording_id.strip():
        return GetSummaryOutput(success=False, error="recording_id is required.")

    path = quote(recording_id.strip(), safe="")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_FATHOM_API_BASE}/recordings/{path}/summary", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return GetSummaryOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetSummaryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSummaryOutput(success=False, error=f"Get summary failed: {exc}")

    # The documented body nests the recap under "summary"; fall back to the
    # top level so a flattened payload still parses.
    nested = data.get("summary")
    summary = _parse_summary(nested if isinstance(nested, dict) else data)
    return GetSummaryOutput(
        success=True,
        template_name=summary.template_name,
        markdown_formatted=summary.markdown_formatted,
    )


@tool(args_schema=GetTranscriptInput)
@serialize_pydantic_return
async def get_transcript(recording_id: str, api_key: str) -> GetTranscriptOutput:
    """Get the full transcript for a specific meeting recording."""
    if not api_key or not api_key.strip():
        return GetTranscriptOutput(success=False, error=_EMPTY_KEY_ERROR)
    if not recording_id or not recording_id.strip():
        return GetTranscriptOutput(success=False, error="recording_id is required.")

    path = quote(recording_id.strip(), safe="")

    try:
        async with httpx.AsyncClient(timeout=_LONG_TIMEOUT) as client:
            response = await client.get(
                f"{_FATHOM_API_BASE}/recordings/{path}/transcript", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return GetTranscriptOutput(success=False, error=_error(response))
        payload = response.json()
    except httpx.TimeoutException:
        return GetTranscriptOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTranscriptOutput(success=False, error=f"Get transcript failed: {exc}")

    # The schema documents {"transcript": [...]}, while the endpoint's own
    # response text calls it "the transcript ... as an array" — accept both.
    raw = payload if isinstance(payload, list) else _as_dict(payload).get("transcript")
    return GetTranscriptOutput(success=True, transcript=_parse_transcript(raw))


@tool(args_schema=ListTeamMembersInput)
@serialize_pydantic_return
async def list_team_members(
    api_key: str,
    team: str | None = None,
    cursor: str | None = None,
) -> ListTeamMembersOutput:
    """List team members in your Fathom organization."""
    if not api_key or not api_key.strip():
        return ListTeamMembersOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if team:
        params["team"] = team.strip()
    if cursor:
        params["cursor"] = cursor.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_FATHOM_API_BASE}/team_members", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListTeamMembersOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListTeamMembersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTeamMembersOutput(success=False, error=f"List team members failed: {exc}")

    return ListTeamMembersOutput(
        success=True,
        members=[
            TeamMember(
                name=_as_str(item.get("name")),
                email=_as_str(item.get("email")),
                created_at=_as_str(item.get("created_at")),
            )
            for item in _dict_list(data.get("items"))
        ],
        next_cursor=_as_str(data.get("next_cursor")),
        limit=_as_int(data.get("limit")),
    )


@tool(args_schema=ListTeamsInput)
@serialize_pydantic_return
async def list_teams(
    api_key: str,
    cursor: str | None = None,
) -> ListTeamsOutput:
    """List teams in your Fathom organization."""
    if not api_key or not api_key.strip():
        return ListTeamsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if cursor:
        params["cursor"] = cursor.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_FATHOM_API_BASE}/teams", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListTeamsOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListTeamsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTeamsOutput(success=False, error=f"List teams failed: {exc}")

    return ListTeamsOutput(
        success=True,
        teams=[
            Team(
                name=_as_str(item.get("name")),
                created_at=_as_str(item.get("created_at")),
            )
            for item in _dict_list(data.get("items"))
        ],
        next_cursor=_as_str(data.get("next_cursor")),
        limit=_as_int(data.get("limit")),
    )
