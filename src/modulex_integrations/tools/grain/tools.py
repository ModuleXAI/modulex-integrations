"""Grain LangChain ``@tool`` functions.

Nine async tools wrapping the Grain public REST API
(``api.grain.com/_/public-api``). The modulex ``ToolExecutor`` injects
an ``api_key: str`` directly (resolved from the user's ``api_key``
credential), not an ``auth_type``/``auth_data`` pair.

Error model: every call is wrapped in try/except, returning the typed
output with ``success=False`` + ``error`` for non-2xx responses,
timeouts, and unexpected exceptions. Non-2xx HTTP responses do *not*
raise.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.grain.outputs import (
    CreateHookOutput,
    DeleteHookOutput,
    GetRecordingOutput,
    GetTranscriptOutput,
    Hook,
    ListHooksOutput,
    ListMeetingTypesOutput,
    ListRecordingsOutput,
    ListTeamsOutput,
    ListViewsOutput,
    MeetingType,
    Recording,
    Team,
    TranscriptSection,
    View,
)

__all__ = [
    "create_hook",
    "delete_hook",
    "get_recording",
    "get_transcript",
    "list_hooks",
    "list_meeting_types",
    "list_recordings",
    "list_teams",
    "list_views",
]

_BASE_URL = "https://api.grain.com/_/public-api"
_API_VERSION = "2025-10-31"
_TIMEOUT = 30.0


# --- Auth helpers ----------------------------------------------------------


def _headers(api_key: str, *, versioned: bool = True) -> dict[str, str]:
    headers: dict[str, str] = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    if versioned:
        headers["Public-Api-Version"] = _API_VERSION
    return headers


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListRecordingsInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")
    cursor: str | None = Field(
        default=None,
        description="Pagination cursor for next page (returned from previous response)",
    )
    before_datetime: str | None = Field(
        default=None,
        description='Only recordings before this ISO8601 timestamp (e.g., "2024-01-15T00:00:00Z")',
    )
    after_datetime: str | None = Field(
        default=None,
        description='Only recordings after this ISO8601 timestamp (e.g., "2024-01-01T00:00:00Z")',
    )
    participant_scope: str | None = Field(
        default=None, description='Filter: "internal" or "external"'
    )
    title_search: str | None = Field(
        default=None,
        description='Search term to filter by recording title (e.g., "weekly standup")',
    )
    team_id: str | None = Field(default=None, description="Filter by team UUID")
    meeting_type_id: str | None = Field(
        default=None, description="Filter by meeting type UUID"
    )
    include_highlights: bool = Field(
        default=False, description="Include highlights/clips in response"
    )
    include_participants: bool = Field(
        default=False, description="Include participant list in response"
    )
    include_ai_summary: bool = Field(
        default=False, description="Include AI-generated summary"
    )


class GetRecordingInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")
    recording_id: str = Field(description="The recording UUID")
    include_highlights: bool = Field(default=False, description="Include highlights/clips")
    include_participants: bool = Field(default=False, description="Include participant list")
    include_ai_summary: bool = Field(default=False, description="Include AI summary")
    include_calendar_event: bool = Field(
        default=False, description="Include calendar event data"
    )
    include_hubspot: bool = Field(default=False, description="Include HubSpot associations")


class GetTranscriptInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")
    recording_id: str = Field(description="The recording UUID")


class ListViewsInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")
    type_filter: str | None = Field(
        default=None,
        description="Optional view type filter: recordings, highlights, or stories",
    )


class ListTeamsInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")


class ListMeetingTypesInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")


class CreateHookInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")
    hook_url: str = Field(
        description='Webhook endpoint URL (e.g., "https://example.com/webhooks/grain")'
    )
    view_id: str = Field(description="Grain view ID for the webhook subscription")
    actions: list[str] | None = Field(
        default=None,
        description="Optional list of actions to subscribe to: added, updated, removed",
    )


class ListHooksInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")


class DeleteHookInput(BaseModel):
    api_key: str = Field(description="Grain API key (provided by credential system)")
    hook_id: str = Field(description="The hook UUID to delete")


# --- Parsing helpers -------------------------------------------------------


def _parse_recording(data: dict[str, Any]) -> Recording:
    return Recording(
        id=data.get("id"),
        title=data.get("title"),
        start_datetime=data.get("start_datetime"),
        end_datetime=data.get("end_datetime"),
        duration_ms=data.get("duration_ms"),
        media_type=data.get("media_type"),
        source=data.get("source"),
        url=data.get("url"),
        thumbnail_url=data.get("thumbnail_url"),
        tags=data.get("tags") or [],
        teams=data.get("teams") or [],
        meeting_type=data.get("meeting_type"),
        highlights=data.get("highlights"),
        participants=data.get("participants"),
        ai_summary=data.get("ai_summary"),
        calendar_event=data.get("calendar_event"),
        hubspot=data.get("hubspot"),
        private_notes=data.get("private_notes"),
        ai_template_sections=data.get("ai_template_sections"),
    )


def _parse_hook(data: dict[str, Any]) -> Hook:
    return Hook(
        id=data.get("id"),
        enabled=data.get("enabled"),
        version=data.get("version"),
        hook_url=data.get("hook_url"),
        view_id=data.get("view_id"),
        actions=data.get("actions") or [],
        inserted_at=data.get("inserted_at"),
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListRecordingsInput)
@serialize_pydantic_return
async def list_recordings(
    api_key: str,
    cursor: str | None = None,
    before_datetime: str | None = None,
    after_datetime: str | None = None,
    participant_scope: str | None = None,
    title_search: str | None = None,
    team_id: str | None = None,
    meeting_type_id: str | None = None,
    include_highlights: bool = False,
    include_participants: bool = False,
    include_ai_summary: bool = False,
) -> ListRecordingsOutput:
    """List recordings from Grain with optional filters and pagination."""
    if not api_key or not api_key.strip():
        return ListRecordingsOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )

    body: dict[str, Any] = {}
    if cursor:
        body["cursor"] = cursor

    filter_: dict[str, Any] = {}
    if before_datetime:
        filter_["before_datetime"] = before_datetime
    if after_datetime:
        filter_["after_datetime"] = after_datetime
    if participant_scope:
        filter_["participant_scope"] = participant_scope
    if title_search:
        filter_["title_search"] = title_search
    if team_id:
        filter_["team"] = team_id
    if meeting_type_id:
        filter_["meeting_type"] = meeting_type_id
    if filter_:
        body["filter"] = filter_

    include: dict[str, Any] = {}
    if include_highlights:
        include["highlights"] = True
    if include_participants:
        include["participants"] = True
    if include_ai_summary:
        include["ai_summary"] = True
    if include:
        body["include"] = include

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/recordings", headers=_headers(api_key), json=body
            )
        if response.status_code != 200:
            return ListRecordingsOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListRecordingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListRecordingsOutput(success=False, error=f"List recordings failed: {exc}")

    return ListRecordingsOutput(
        success=True,
        recordings=[_parse_recording(item) for item in data.get("recordings") or []],
        cursor=data.get("cursor"),
    )


@tool(args_schema=GetRecordingInput)
@serialize_pydantic_return
async def get_recording(
    api_key: str,
    recording_id: str,
    include_highlights: bool = False,
    include_participants: bool = False,
    include_ai_summary: bool = False,
    include_calendar_event: bool = False,
    include_hubspot: bool = False,
) -> GetRecordingOutput:
    """Get details of a single recording by ID."""
    if not api_key or not api_key.strip():
        return GetRecordingOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )
    if not recording_id or not recording_id.strip():
        return GetRecordingOutput(success=False, error="Recording ID is required.")

    include: dict[str, Any] = {}
    if include_highlights:
        include["highlights"] = True
    if include_participants:
        include["participants"] = True
    if include_ai_summary:
        include["ai_summary"] = True
    if include_calendar_event:
        include["calendar_event"] = True
    if include_hubspot:
        include["hubspot"] = True
    body: dict[str, Any] = {"include": include} if include else {}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/recordings/{recording_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code != 200:
            return GetRecordingOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetRecordingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetRecordingOutput(success=False, error=f"Get recording failed: {exc}")

    return GetRecordingOutput(success=True, recording=_parse_recording(data or {}))


@tool(args_schema=GetTranscriptInput)
@serialize_pydantic_return
async def get_transcript(api_key: str, recording_id: str) -> GetTranscriptOutput:
    """Get the full transcript of a recording."""
    if not api_key or not api_key.strip():
        return GetTranscriptOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )
    if not recording_id or not recording_id.strip():
        return GetTranscriptOutput(success=False, error="Recording ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v2/recordings/{recording_id.strip()}/transcript",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return GetTranscriptOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetTranscriptOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTranscriptOutput(success=False, error=f"Get transcript failed: {exc}")

    # API returns the transcript array directly.
    sections = data if isinstance(data, list) else []
    return GetTranscriptOutput(
        success=True,
        transcript=[
            TranscriptSection(
                participant_id=item.get("participant_id"),
                speaker=item.get("speaker"),
                start=item.get("start"),
                end=item.get("end"),
                text=item.get("text"),
            )
            for item in sections
        ],
    )


@tool(args_schema=ListViewsInput)
@serialize_pydantic_return
async def list_views(api_key: str, type_filter: str | None = None) -> ListViewsOutput:
    """List available Grain views for webhook subscriptions."""
    if not api_key or not api_key.strip():
        return ListViewsOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )

    params: dict[str, Any] = {}
    if type_filter:
        params["type_filter"] = type_filter

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # TODO (unverified): the views endpoint path is the unversioned
            # /_/public-api/views per the source bundle; the official API
            # overview lists v2-prefixed paths but the views reference page
            # is gated, so this could not be re-confirmed. Per developers.grain.com.
            response = await client.get(
                f"{_BASE_URL}/views",
                headers=_headers(api_key, versioned=False),
                params=params,
            )
        if response.status_code != 200:
            return ListViewsOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListViewsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListViewsOutput(success=False, error=f"List views failed: {exc}")

    if isinstance(data, dict):
        raw = data.get("views") or []
    elif isinstance(data, list):
        raw = data
    else:
        raw = []
    return ListViewsOutput(
        success=True,
        views=[
            View(id=item.get("id"), name=item.get("name"), type=item.get("type"))
            for item in raw
        ],
    )


@tool(args_schema=ListTeamsInput)
@serialize_pydantic_return
async def list_teams(api_key: str) -> ListTeamsOutput:
    """List all teams in the workspace."""
    if not api_key or not api_key.strip():
        return ListTeamsOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/teams", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListTeamsOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTeamsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTeamsOutput(success=False, error=f"List teams failed: {exc}")

    if isinstance(data, dict):
        raw = data.get("teams") or []
    elif isinstance(data, list):
        raw = data
    else:
        raw = []
    return ListTeamsOutput(
        success=True,
        teams=[Team(id=item.get("id"), name=item.get("name")) for item in raw],
    )


@tool(args_schema=ListMeetingTypesInput)
@serialize_pydantic_return
async def list_meeting_types(api_key: str) -> ListMeetingTypesOutput:
    """List all meeting types in the workspace."""
    if not api_key or not api_key.strip():
        return ListMeetingTypesOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/meeting_types", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return ListMeetingTypesOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListMeetingTypesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMeetingTypesOutput(
            success=False, error=f"List meeting types failed: {exc}"
        )

    if isinstance(data, dict):
        raw = data.get("meeting_types") or []
    elif isinstance(data, list):
        raw = data
    else:
        raw = []
    return ListMeetingTypesOutput(
        success=True,
        meeting_types=[
            MeetingType(
                id=item.get("id"), name=item.get("name"), scope=item.get("scope")
            )
            for item in raw
        ],
    )


@tool(args_schema=CreateHookInput)
@serialize_pydantic_return
async def create_hook(
    api_key: str,
    hook_url: str,
    view_id: str,
    actions: list[str] | None = None,
) -> CreateHookOutput:
    """Create a webhook to receive recording events."""
    if not api_key or not api_key.strip():
        return CreateHookOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )
    if not hook_url or not hook_url.strip():
        return CreateHookOutput(success=False, error="Webhook URL is required.")
    if not view_id or not view_id.strip():
        return CreateHookOutput(success=False, error="View ID is required.")

    body: dict[str, Any] = {
        "version": 2,
        "hook_url": hook_url.strip(),
        "view_id": view_id.strip(),
    }
    if actions:
        body["actions"] = actions

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # TODO (unverified): the hooks endpoint path is the unversioned
            # /_/public-api/hooks per the source bundle; the official API
            # overview lists /_/public-api/v2/hooks/create but the hooks
            # reference page is gated and could not be re-confirmed.
            # Per developers.grain.com.
            response = await client.post(
                f"{_BASE_URL}/hooks",
                headers=_headers(api_key, versioned=False),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateHookOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateHookOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateHookOutput(success=False, error=f"Create webhook failed: {exc}")

    if not isinstance(data, dict) or not data.get("id"):
        return CreateHookOutput(
            success=False,
            error="Webhook created but response did not include a webhook id.",
        )
    return CreateHookOutput(success=True, hook=_parse_hook(data))


@tool(args_schema=ListHooksInput)
@serialize_pydantic_return
async def list_hooks(api_key: str) -> ListHooksOutput:
    """List all webhooks for the account."""
    if not api_key or not api_key.strip():
        return ListHooksOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # TODO (unverified): the hooks endpoint path is the unversioned
            # /_/public-api/hooks per the source bundle; the official API
            # overview lists v2-prefixed hook paths but the hooks reference
            # page is gated and could not be re-confirmed. Per developers.grain.com.
            response = await client.get(
                f"{_BASE_URL}/hooks", headers=_headers(api_key, versioned=False)
            )
        if response.status_code != 200:
            return ListHooksOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListHooksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListHooksOutput(success=False, error=f"List webhooks failed: {exc}")

    if isinstance(data, dict):
        raw = data.get("hooks") or []
    elif isinstance(data, list):
        raw = data
    else:
        raw = []
    return ListHooksOutput(success=True, hooks=[_parse_hook(item) for item in raw])


@tool(args_schema=DeleteHookInput)
@serialize_pydantic_return
async def delete_hook(api_key: str, hook_id: str) -> DeleteHookOutput:
    """Delete a webhook by ID."""
    if not api_key or not api_key.strip():
        return DeleteHookOutput(
            success=False,
            error="Grain API key is empty. Please configure a valid Grain credential.",
        )
    if not hook_id or not hook_id.strip():
        return DeleteHookOutput(success=False, error="Webhook ID is required.")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            # TODO (unverified): the hooks endpoint path is the unversioned
            # /_/public-api/hooks/:id per the source bundle; the official API
            # overview lists /_/public-api/v2/hooks/:id but the hooks
            # reference page is gated and could not be re-confirmed.
            # Per developers.grain.com.
            response = await client.delete(
                f"{_BASE_URL}/hooks/{hook_id.strip()}",
                headers=_headers(api_key, versioned=False),
            )
        if response.status_code not in (200, 202, 204):
            return DeleteHookOutput(
                success=False,
                error=f"Grain API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteHookOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteHookOutput(success=False, error=f"Delete webhook failed: {exc}")

    return DeleteHookOutput(success=True)
