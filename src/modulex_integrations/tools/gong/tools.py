"""Gong LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.gong.outputs import (
    AddNewCallOutput,
    GetExtensiveDataOutput,
    ListCallsOutput,
    ListWorkspaceIdOptionsOutput,
    RetrieveTranscriptsOfCallsOutput,
    Workspace,
)

__all__ = [
    "add_new_call",
    "get_extensive_data",
    "list_calls",
    "list_workspace_id_options",
    "retrieve_transcripts_of_calls",
]

_BASE_URL = "https://us-66463.api.gong.io/v2"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Gong API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class AddNewCallInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    client_unique_id: str = Field(description="A call's unique identifier in the PBX or recording system")
    actual_start: str = Field(description="Actual start date/time in ISO-8601 format")
    direction: str = Field(description="Call direction: Inbound, Outbound, Conference, or Unknown")
    primary_user: str = Field(description="Gong internal user ID of the call host")
    parties: list[dict[str, Any]] = Field(description="List of call participants as objects with phoneNumber, emailAddress, name, mediaChannelId")
    title: str | None = Field(default=None, description="Title of the call")
    purpose: str | None = Field(default=None, description="Purpose of the call, up to 255 characters")
    scheduled_start: str | None = Field(default=None, description="Scheduled start in ISO-8601 format")
    scheduled_end: str | None = Field(default=None, description="Scheduled end in ISO-8601 format")
    duration: int | None = Field(default=None, description="Actual call duration in seconds")
    disposition: str | None = Field(default=None, description="Disposition of the call, up to 255 characters")
    meeting_url: str | None = Field(default=None, description="Conference call URL")
    call_provider_code: str | None = Field(default=None, description="Provider code: zoom, clearslide, gotomeeting, ringcentral, outreach, insidesales")
    download_media_url: str | None = Field(default=None, description="URL for Gong to download the media file")
    workspace_id: str | None = Field(default=None, description="Workspace identifier for call placement")
    language_code: str | None = Field(default=None, description="Language code for transcription (e.g., en-US)")


class GetExtensiveDataInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_date_time: str | None = Field(default=None, description="Start date/time in ISO-8601 format")
    to_date_time: str | None = Field(default=None, description="End date/time in ISO-8601 format")
    workspace_id: str | None = Field(default=None, description="Workspace ID to filter by")
    call_ids: list[str] | None = Field(default=None, description="List of call IDs to filter")
    primary_user_ids: list[str] | None = Field(default=None, description="List of user IDs to filter by host")
    max_results: int = Field(default=600, description="Maximum number of results to return")
    context: str = Field(default="None", description="Context level: None, Basic, or Extended")
    context_timing: list[str] | None = Field(default=None, description="Timing for context data: Now or TimeOfCall")
    include_parties: bool = Field(default=False, description="Whether to include parties")
    exposed_fields_content: dict[str, bool] | None = Field(default=None, description="Content fields to include")
    exposed_fields_interaction: dict[str, bool] | None = Field(default=None, description="Interaction fields to include")
    include_public_comments: bool = Field(default=False, description="Whether to include public comments")
    include_media: bool = Field(default=False, description="Whether to include media")


class ListCallsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_date_time: str | None = Field(default=None, description="Start date/time in ISO-8601 format")
    to_date_time: str | None = Field(default=None, description="End date/time in ISO-8601 format")
    cursor: str | None = Field(default=None, description="Pagination cursor from a previous call")


class ListWorkspaceIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class RetrieveTranscriptsOfCallsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    from_date_time: str | None = Field(default=None, description="Start date/time in ISO-8601 format")
    to_date_time: str | None = Field(default=None, description="End date/time in ISO-8601 format")
    workspace_id: str | None = Field(default=None, description="Workspace ID to filter by")
    call_ids: list[str] | None = Field(default=None, description="List of call IDs to retrieve transcripts for")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AddNewCallInput)
@serialize_pydantic_return
async def add_new_call(
    auth_type: str,
    auth_data: dict[str, Any],
    client_unique_id: str,
    actual_start: str,
    direction: str,
    primary_user: str,
    parties: list[dict[str, Any]],
    title: str | None = None,
    purpose: str | None = None,
    scheduled_start: str | None = None,
    scheduled_end: str | None = None,
    duration: int | None = None,
    disposition: str | None = None,
    meeting_url: str | None = None,
    call_provider_code: str | None = None,
    download_media_url: str | None = None,
    workspace_id: str | None = None,
    language_code: str | None = None,
) -> AddNewCallOutput:
    """Add a new call to Gong."""
    if not auth_data.get("access_token"):
        return AddNewCallOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    payload: dict[str, Any] = {
        "clientUniqueId": client_unique_id,
        "actualStart": actual_start,
        "direction": direction,
        "primaryUser": primary_user,
        "parties": parties,
    }
    if title is not None:
        payload["title"] = title
    if purpose is not None:
        payload["purpose"] = purpose
    if scheduled_start is not None:
        payload["scheduledStart"] = scheduled_start
    if scheduled_end is not None:
        payload["scheduledEnd"] = scheduled_end
    if duration is not None:
        payload["duration"] = duration
    if disposition is not None:
        payload["disposition"] = disposition
    if meeting_url is not None:
        payload["meetingUrl"] = meeting_url
    if call_provider_code is not None:
        payload["callProviderCode"] = call_provider_code
    if download_media_url is not None:
        payload["downloadMediaUrl"] = download_media_url
    if workspace_id is not None:
        payload["workspaceId"] = workspace_id
    if language_code is not None:
        payload["languageCode"] = language_code

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/calls",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return AddNewCallOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddNewCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddNewCallOutput(success=False, error=f"Call failed: {exc}")

    return AddNewCallOutput(
        success=True,
        request_id=data.get("requestId"),
        call_id=data.get("callId"),
    )


@tool(args_schema=GetExtensiveDataInput)
@serialize_pydantic_return
async def get_extensive_data(
    auth_type: str,
    auth_data: dict[str, Any],
    from_date_time: str | None = None,
    to_date_time: str | None = None,
    workspace_id: str | None = None,
    call_ids: list[str] | None = None,
    primary_user_ids: list[str] | None = None,
    max_results: int = 600,
    context: str = "None",
    context_timing: list[str] | None = None,
    include_parties: bool = False,
    exposed_fields_content: dict[str, bool] | None = None,
    exposed_fields_interaction: dict[str, bool] | None = None,
    include_public_comments: bool = False,
    include_media: bool = False,
) -> GetExtensiveDataOutput:
    """List detailed call data with content selectors for topics, trackers, transcripts, and more."""
    if not auth_data.get("access_token"):
        return GetExtensiveDataOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    payload: dict[str, Any] = {}

    filter_obj: dict[str, Any] = {}
    if from_date_time is not None:
        filter_obj["fromDateTime"] = from_date_time
    if to_date_time is not None:
        filter_obj["toDateTime"] = to_date_time
    if workspace_id is not None:
        filter_obj["workspaceId"] = workspace_id
    if call_ids is not None:
        filter_obj["callIds"] = call_ids
    if primary_user_ids is not None:
        filter_obj["primaryUserIds"] = primary_user_ids
    if filter_obj:
        payload["filter"] = filter_obj

    content_selector: dict[str, Any] = {}
    if context != "None":
        content_selector["context"] = context
    if context_timing is not None:
        content_selector["contextTiming"] = context_timing
    if include_parties:
        content_selector["includeParties"] = True
    if exposed_fields_content is not None:
        content_selector["exposedFields"] = content_selector.get("exposedFields", {})
        content_selector["exposedFields"]["content"] = exposed_fields_content
    if exposed_fields_interaction is not None:
        content_selector["exposedFields"] = content_selector.get("exposedFields", {})
        content_selector["exposedFields"]["interaction"] = exposed_fields_interaction
    if include_public_comments:
        content_selector["includePublicComments"] = True
    if include_media:
        content_selector["includeMedia"] = True
    if content_selector:
        payload["contentSelector"] = content_selector

    all_calls: list[dict[str, Any]] = []
    cursor: str | None = None
    collected = 0

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while collected < max_results:
                request_payload = dict(payload)
                if cursor is not None:
                    request_payload["cursor"] = cursor

                response = await client.post(
                    f"{_BASE_URL}/calls/extensive",
                    headers=headers,
                    json=request_payload,
                )
                if response.status_code != 200:
                    return GetExtensiveDataOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                data = response.json()
                calls = data.get("calls", [])
                all_calls.extend(calls)
                collected += len(calls)

                records = data.get("records", {})
                cursor = records.get("cursor")
                if not cursor or not calls:
                    break
    except httpx.TimeoutException:
        return GetExtensiveDataOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetExtensiveDataOutput(success=False, error=f"Call failed: {exc}")

    return GetExtensiveDataOutput(success=True, calls=all_calls[:max_results])


@tool(args_schema=ListCallsInput)
@serialize_pydantic_return
async def list_calls(
    auth_type: str,
    auth_data: dict[str, Any],
    from_date_time: str | None = None,
    to_date_time: str | None = None,
    cursor: str | None = None,
) -> ListCallsOutput:
    """List calls with optional date range filtering."""
    if not auth_data.get("access_token"):
        return ListCallsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    params: dict[str, str] = {}
    if from_date_time is not None:
        params["fromDateTime"] = from_date_time
    if to_date_time is not None:
        params["toDateTime"] = to_date_time
    if cursor is not None:
        params["cursor"] = cursor

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/calls",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListCallsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCallsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCallsOutput(success=False, error=f"Call failed: {exc}")

    return ListCallsOutput(
        success=True,
        request_id=data.get("requestId"),
        cursor=(data.get("records") or {}).get("cursor"),
        calls=data.get("calls", []),
    )


@tool(args_schema=ListWorkspaceIdOptionsInput)
@serialize_pydantic_return
async def list_workspace_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListWorkspaceIdOptionsOutput:
    """Retrieve available workspace IDs and names."""
    if not auth_data.get("access_token"):
        return ListWorkspaceIdOptionsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/workspaces",
                headers=headers,
            )
        if response.status_code != 200:
            return ListWorkspaceIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListWorkspaceIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorkspaceIdOptionsOutput(success=False, error=f"Call failed: {exc}")

    raw_workspaces = data.get("workspaces", [])
    workspaces = [
        Workspace(id=w.get("id"), name=w.get("name"))
        for w in raw_workspaces
    ]
    return ListWorkspaceIdOptionsOutput(success=True, workspaces=workspaces)


@tool(args_schema=RetrieveTranscriptsOfCallsInput)
@serialize_pydantic_return
async def retrieve_transcripts_of_calls(
    auth_type: str,
    auth_data: dict[str, Any],
    from_date_time: str | None = None,
    to_date_time: str | None = None,
    workspace_id: str | None = None,
    call_ids: list[str] | None = None,
) -> RetrieveTranscriptsOfCallsOutput:
    """Retrieve transcripts of calls with optional date range and call ID filtering."""
    if not auth_data.get("access_token"):
        return RetrieveTranscriptsOfCallsOutput(success=False, error="Missing or empty access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"

    filter_obj: dict[str, Any] = {}
    if from_date_time is not None:
        filter_obj["fromDateTime"] = from_date_time
    if to_date_time is not None:
        filter_obj["toDateTime"] = to_date_time
    if workspace_id is not None:
        filter_obj["workspaceId"] = workspace_id
    if call_ids is not None:
        filter_obj["callIds"] = call_ids

    payload: dict[str, Any] = {}
    if filter_obj:
        payload["filter"] = filter_obj

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/calls/transcript",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return RetrieveTranscriptsOfCallsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RetrieveTranscriptsOfCallsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RetrieveTranscriptsOfCallsOutput(success=False, error=f"Call failed: {exc}")

    return RetrieveTranscriptsOfCallsOutput(
        success=True,
        call_transcripts=data.get("callTranscripts", []),
    )
