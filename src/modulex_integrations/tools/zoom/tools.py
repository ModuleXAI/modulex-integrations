"""Zoom LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.zoom.outputs import (
    AddMeetingRegistrantOutput,
    AddWebinarRegistrantOutput,
    CreateMeetingOutput,
    CreateUserOutput,
    DeleteMeetingOutput,
    DeleteUserOutput,
    GetCurrentUserOutput,
    GetMeetingDetailsOutput,
    GetMeetingRecordingsOutput,
    GetMeetingSummaryOutput,
    GetMeetingTranscriptOutput,
    GetWebinarDetailsOutput,
    ListAllRecordingsOutput,
    ListCallRecordingsOutput,
    ListChannelsOutput,
    ListMeetingsOutput,
    ListPastMeetingParticipantsOutput,
    ListPastWebinarQaOutput,
    ListUserCallLogsOutput,
    ListWebinarParticipantsReportOutput,
    MeetingSummary,
    MeetingWebinarItem,
    ParticipantItem,
    QaItem,
    RecordingFile,
    RecordingMeeting,
    RegistrantResponse,
    SendChatMessageOutput,
    UpdateMeetingOutput,
    UpdateWebinarOutput,
    UserInfo,
)

__all__ = [
    "add_meeting_registrant",
    "add_webinar_registrant",
    "create_meeting",
    "create_user",
    "delete_meeting",
    "delete_user",
    "get_current_user",
    "get_meeting_details",
    "get_meeting_recordings",
    "get_meeting_summary",
    "get_meeting_transcript",
    "get_webinar_details",
    "list_all_recordings",
    "list_call_recordings",
    "list_channels",
    "list_meetings",
    "list_past_meeting_participants",
    "list_past_webinar_qa",
    "list_user_call_logs",
    "list_webinar_participants_report",
    "send_chat_message",
    "update_meeting",
    "update_webinar",
]

_BASE_URL = "https://api.zoom.us/v2"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Zoom API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class CreateMeetingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    topic: str | None = Field(default=None, description="Meeting topic")
    type: int | None = Field(default=None, description="Meeting type: 1 - Instant, 2 - Scheduled, 3 - Recurring no fixed time, 8 - Recurring fixed time")
    start_time: str | None = Field(default=None, description="Meeting start time in yyyy-MM-ddTHH:mm:ssZ or yyyy-MM-ddTHH:mm:ss format")
    duration: int | None = Field(default=None, description="Meeting duration in minutes")
    timezone: str | None = Field(default=None, description="Time zone for start_time")
    password: str | None = Field(default=None, description="Password to join, max 10 characters")
    agenda: str | None = Field(default=None, description="Meeting description/agenda")


class ListMeetingsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="The user ID or email. Use 'me' for the current user.")
    type: str | None = Field(default=None, description="Type: scheduled, live, upcoming, previous_meetings")


class GetMeetingDetailsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The meeting ID")
    occurrence_id: str | None = Field(default=None, description="Meeting occurrence ID")


class UpdateMeetingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The Zoom meeting ID to update")
    topic: str | None = Field(default=None, description="Meeting topic")
    type: int | None = Field(default=None, description="Meeting type")
    start_time: str | None = Field(default=None, description="Meeting start time")
    duration: int | None = Field(default=None, description="Meeting duration in minutes")
    timezone: str | None = Field(default=None, description="Time zone for start_time")
    password: str | None = Field(default=None, description="Password to join")
    agenda: str | None = Field(default=None, description="Meeting description/agenda")


class DeleteMeetingInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The ID of the meeting to delete")
    occurrence_id: str | None = Field(default=None, description="Occurrence ID to delete only that instance")
    schedule_for_reminder: bool | None = Field(default=None, description="Notify host about cancellation")
    cancel_meeting_reminder: bool | None = Field(default=None, description="Notify registrants about cancellation")


class GetCurrentUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class SendChatMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    message: str = Field(description="The message to be sent")
    to_contact: str | None = Field(default=None, description="Email address of the contact")
    to_channel: str | None = Field(default=None, description="Channel ID to send the message to")


class ListChannelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    page_size: int | None = Field(default=None, description="Number of records per page")
    next_page_token: str | None = Field(default=None, description="Next page token for pagination")


class AddMeetingRegistrantInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The meeting ID")
    email: str = Field(description="Registrant's email address")
    first_name: str = Field(description="Registrant's first name")
    last_name: str = Field(description="Registrant's last name")
    occurrence_ids: str | None = Field(default=None, description="Occurrence IDs, comma separated")


class GetMeetingRecordingsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The meeting ID")
    download_access_token: bool | None = Field(default=None, description="Include download access token")


class GetMeetingTranscriptInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The meeting ID")


class GetMeetingSummaryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The meeting ID or UUID")


class ListAllRecordingsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(default="me", description="User ID or email. Use 'me' for the current user.")
    from_date: str | None = Field(default=None, description="Start date in yyyy-MM-dd format")
    to_date: str | None = Field(default=None, description="End date in yyyy-MM-dd format")
    trash: bool | None = Field(default=None, description="If true, list recordings from trash")


class ListCallRecordingsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start_date: str | None = Field(default=None, description="Start date in yyyy-MM-dd or yyyy-MM-ddTHH:mm:ssZ format")
    end_date: str | None = Field(default=None, description="End date, max 30-day range")


class ListUserCallLogsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="The user ID or email address")


class ListPastMeetingParticipantsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    meeting_id: str = Field(description="The meeting ID")


class CreateUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    action: str = Field(description="How to create the user: create, autoCreate, custCreate, ssoCreate")
    email: str = Field(description="User's email address")
    type: int = Field(description="User type: 1 - Basic, 2 - Licensed, 3 - On-prem")
    first_name: str | None = Field(default=None, description="User's first name")
    last_name: str | None = Field(default=None, description="User's last name")


class DeleteUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str = Field(description="The user ID or email address")
    action: str | None = Field(default=None, description="Delete action: disassociate or delete")
    transfer_email: str | None = Field(default=None, description="Email to transfer resources to")
    transfer_meeting: bool | None = Field(default=None, description="Transfer meetings")
    transfer_webinar: bool | None = Field(default=None, description="Transfer webinars")
    transfer_recording: bool | None = Field(default=None, description="Transfer recordings")


class GetWebinarDetailsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    webinar_id: str = Field(description="The webinar ID")
    occurrence_id: str | None = Field(default=None, description="Occurrence ID for recurring webinar")


class UpdateWebinarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    webinar_id: str = Field(description="The Zoom webinar ID to update")
    topic: str | None = Field(default=None, description="Webinar topic")
    type: int | None = Field(default=None, description="Webinar type")
    start_time: str | None = Field(default=None, description="Webinar start time")
    duration: int | None = Field(default=None, description="Webinar duration in minutes")
    timezone: str | None = Field(default=None, description="Time zone for start_time")
    password: str | None = Field(default=None, description="Password to join the webinar")
    agenda: str | None = Field(default=None, description="Webinar description/agenda")


class AddWebinarRegistrantInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    webinar_id: str = Field(description="The webinar ID")
    email: str = Field(description="Registrant's email address")
    first_name: str = Field(description="Registrant's first name")
    last_name: str = Field(description="Registrant's last name")
    occurrence_ids: str | None = Field(default=None, description="Occurrence IDs, comma separated")


class ListWebinarParticipantsReportInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    webinar_id: str = Field(description="The webinar ID")


class ListPastWebinarQaInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    webinar_id: str = Field(description="The Zoom webinar ID")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateMeetingInput)
@serialize_pydantic_return
async def create_meeting(
    auth_type: str,
    auth_data: dict[str, Any],
    topic: str | None = None,
    type: int | None = None,
    start_time: str | None = None,
    duration: int | None = None,
    timezone: str | None = None,
    password: str | None = None,
    agenda: str | None = None,
) -> CreateMeetingOutput:
    """Create a meeting for the authenticated user. A maximum of 100 meetings can be created per day."""
    if not auth_data.get("access_token"):
        return CreateMeetingOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if topic is not None:
        body["topic"] = topic
    if type is not None:
        body["type"] = type
    if start_time is not None:
        body["start_time"] = start_time
    if duration is not None:
        body["duration"] = duration
    if timezone is not None:
        body["timezone"] = timezone
    if password is not None:
        body["password"] = password
    if agenda is not None:
        body["agenda"] = agenda
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/users/me/meetings",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateMeetingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateMeetingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateMeetingOutput(success=False, error=f"Call failed: {exc}")
    return CreateMeetingOutput(
        success=True,
        id=data.get("id"),
        uuid=data.get("uuid"),
        topic=data.get("topic"),
        start_time=data.get("start_time"),
        join_url=data.get("join_url"),
        password=data.get("password"),
        start_url=data.get("start_url"),
    )


@tool(args_schema=ListMeetingsInput)
@serialize_pydantic_return
async def list_meetings(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str = "me",
    type: str | None = None,
) -> ListMeetingsOutput:
    """List meetings for a user."""
    if not auth_data.get("access_token"):
        return ListMeetingsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if type is not None:
        params["type"] = type
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/users/{user_id}/meetings",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListMeetingsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListMeetingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMeetingsOutput(success=False, error=f"Call failed: {exc}")
    meetings = [
        MeetingWebinarItem(
            id=m.get("id"),
            uuid=m.get("uuid"),
            topic=m.get("topic"),
            type=m.get("type"),
            start_time=m.get("start_time"),
            duration=m.get("duration"),
            timezone=m.get("timezone"),
            join_url=m.get("join_url"),
            status=m.get("status"),
        )
        for m in data.get("meetings", [])
    ]
    return ListMeetingsOutput(
        success=True,
        meetings=meetings,
        total_records=data.get("total_records"),
    )


@tool(args_schema=GetMeetingDetailsInput)
@serialize_pydantic_return
async def get_meeting_details(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
    occurrence_id: str | None = None,
) -> GetMeetingDetailsOutput:
    """Retrieve the details of a meeting."""
    if not auth_data.get("access_token"):
        return GetMeetingDetailsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if occurrence_id is not None:
        params["occurrence_id"] = occurrence_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meetings/{meeting_id}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GetMeetingDetailsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMeetingDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMeetingDetailsOutput(success=False, error=f"Call failed: {exc}")
    return GetMeetingDetailsOutput(
        success=True,
        id=data.get("id"),
        uuid=data.get("uuid"),
        topic=data.get("topic"),
        type=data.get("type"),
        start_time=data.get("start_time"),
        duration=data.get("duration"),
        timezone=data.get("timezone"),
        join_url=data.get("join_url"),
        password=data.get("password"),
        status=data.get("status"),
        host_email=data.get("host_email"),
    )


@tool(args_schema=UpdateMeetingInput)
@serialize_pydantic_return
async def update_meeting(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
    topic: str | None = None,
    type: int | None = None,
    start_time: str | None = None,
    duration: int | None = None,
    timezone: str | None = None,
    password: str | None = None,
    agenda: str | None = None,
) -> UpdateMeetingOutput:
    """Update an existing Zoom meeting's topic, time, or other settings."""
    if not auth_data.get("access_token"):
        return UpdateMeetingOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if topic is not None:
        body["topic"] = topic
    if type is not None:
        body["type"] = type
    if start_time is not None:
        body["start_time"] = start_time
    if duration is not None:
        body["duration"] = duration
    if timezone is not None:
        body["timezone"] = timezone
    if password is not None:
        body["password"] = password
    if agenda is not None:
        body["agenda"] = agenda
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/meetings/{meeting_id}",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 204):
            return UpdateMeetingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateMeetingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateMeetingOutput(success=False, error=f"Call failed: {exc}")
    return UpdateMeetingOutput(success=True)


@tool(args_schema=DeleteMeetingInput)
@serialize_pydantic_return
async def delete_meeting(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
    occurrence_id: str | None = None,
    schedule_for_reminder: bool | None = None,
    cancel_meeting_reminder: bool | None = None,
) -> DeleteMeetingOutput:
    """Delete a meeting."""
    if not auth_data.get("access_token"):
        return DeleteMeetingOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if occurrence_id is not None:
        params["occurrence_id"] = occurrence_id
    if schedule_for_reminder is not None:
        params["schedule_for_reminder"] = str(schedule_for_reminder).lower()
    if cancel_meeting_reminder is not None:
        params["cancel_meeting_reminder"] = str(cancel_meeting_reminder).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/meetings/{meeting_id}",
                headers=headers,
                params=params,
            )
        if response.status_code not in (200, 204):
            return DeleteMeetingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteMeetingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteMeetingOutput(success=False, error=f"Call failed: {exc}")
    return DeleteMeetingOutput(success=True)


@tool(args_schema=GetCurrentUserInput)
@serialize_pydantic_return
async def get_current_user(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCurrentUserOutput:
    """Return the authenticated Zoom user's ID, name, email, account ID, and timezone."""
    if not auth_data.get("access_token"):
        return GetCurrentUserOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/users/me",
                headers=headers,
            )
        if response.status_code != 200:
            return GetCurrentUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCurrentUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCurrentUserOutput(success=False, error=f"Call failed: {exc}")
    return GetCurrentUserOutput(
        success=True,
        user=UserInfo(
            id=data.get("id"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            display_name=data.get("display_name"),
            email=data.get("email"),
            account_id=data.get("account_id"),
            timezone=data.get("timezone"),
            type=data.get("type"),
        ),
    )


@tool(args_schema=SendChatMessageInput)
@serialize_pydantic_return
async def send_chat_message(
    auth_type: str,
    auth_data: dict[str, Any],
    message: str,
    to_contact: str | None = None,
    to_channel: str | None = None,
) -> SendChatMessageOutput:
    """Send a chat message on Zoom to an individual contact or a channel."""
    if not auth_data.get("access_token"):
        return SendChatMessageOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"message": message}
    if to_contact is not None:
        body["to_contact"] = to_contact
    if to_channel is not None:
        body["to_channel"] = to_channel
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/chat/users/me/messages",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return SendChatMessageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendChatMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendChatMessageOutput(success=False, error=f"Call failed: {exc}")
    return SendChatMessageOutput(
        success=True,
        id=data.get("id"),
    )


@tool(args_schema=ListChannelsInput)
@serialize_pydantic_return
async def list_channels(
    auth_type: str,
    auth_data: dict[str, Any],
    page_size: int | None = None,
    next_page_token: str | None = None,
) -> ListChannelsOutput:
    """List the authenticated user's chat channels."""
    if not auth_data.get("access_token"):
        return ListChannelsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if page_size is not None:
        params["page_size"] = page_size
    if next_page_token is not None:
        params["next_page_token"] = next_page_token
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/chat/users/me/channels",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListChannelsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListChannelsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListChannelsOutput(success=False, error=f"Call failed: {exc}")
    return ListChannelsOutput(
        success=True,
        channels=data.get("channels", []),
    )


@tool(args_schema=AddMeetingRegistrantInput)
@serialize_pydantic_return
async def add_meeting_registrant(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
    email: str,
    first_name: str,
    last_name: str,
    occurrence_ids: str | None = None,
) -> AddMeetingRegistrantOutput:
    """Register a participant for a meeting."""
    if not auth_data.get("access_token"):
        return AddMeetingRegistrantOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
    }
    params: dict[str, Any] = {}
    if occurrence_ids is not None:
        params["occurrence_ids"] = occurrence_ids
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/meetings/{meeting_id}/registrants",
                headers=headers,
                json=body,
                params=params,
            )
        if response.status_code not in (200, 201):
            return AddMeetingRegistrantOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddMeetingRegistrantOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddMeetingRegistrantOutput(success=False, error=f"Call failed: {exc}")
    return AddMeetingRegistrantOutput(
        success=True,
        registrant=RegistrantResponse(
            id=data.get("id"),
            registrant_id=data.get("registrant_id"),
            start_time=data.get("start_time"),
            join_url=data.get("join_url"),
            topic=data.get("topic"),
        ),
    )


@tool(args_schema=GetMeetingRecordingsInput)
@serialize_pydantic_return
async def get_meeting_recordings(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
    download_access_token: bool | None = None,
) -> GetMeetingRecordingsOutput:
    """Get the recordings of a meeting."""
    if not auth_data.get("access_token"):
        return GetMeetingRecordingsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if download_access_token:
        params["include_fields"] = "download_access_token"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meetings/{meeting_id}/recordings",
                headers=headers,
                params=params,
            )
        if response.status_code == 404:
            return GetMeetingRecordingsOutput(success=True, recording_files=[])
        if response.status_code != 200:
            return GetMeetingRecordingsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMeetingRecordingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMeetingRecordingsOutput(success=False, error=f"Call failed: {exc}")
    files = [
        RecordingFile(
            id=f.get("id"),
            meeting_id=f.get("meeting_id"),
            recording_start=f.get("recording_start"),
            recording_end=f.get("recording_end"),
            file_type=f.get("file_type"),
            file_size=f.get("file_size"),
            download_url=f.get("download_url"),
            play_url=f.get("play_url"),
            status=f.get("status"),
            recording_type=f.get("recording_type"),
        )
        for f in data.get("recording_files", [])
    ]
    return GetMeetingRecordingsOutput(
        success=True,
        recording_files=files,
        download_access_token=data.get("download_access_token"),
    )


@tool(args_schema=GetMeetingTranscriptInput)
@serialize_pydantic_return
async def get_meeting_transcript(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
) -> GetMeetingTranscriptOutput:
    """Get the transcript of a past meeting as speaker-attributed plain text."""
    if not auth_data.get("access_token"):
        return GetMeetingTranscriptOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meetings/{meeting_id}/recordings",
                headers=headers,
                params={"include_fields": "download_access_token"},
            )
        if response.status_code != 200:
            return GetMeetingTranscriptOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
        transcript_file = None
        for f in data.get("recording_files", []):
            if f.get("file_type") == "TRANSCRIPT":
                transcript_file = f
                break
        if not transcript_file:
            return GetMeetingTranscriptOutput(
                success=False,
                error="No transcript file found for this meeting",
            )
        download_url = transcript_file.get("download_url", "")
        token = data.get("download_access_token", "")
        vtt_url = f"{download_url}?access_token={token}" if token else download_url
        async with httpx.AsyncClient(timeout=60.0) as client:
            vtt_response = await client.get(vtt_url)
        if vtt_response.status_code != 200:
            return GetMeetingTranscriptOutput(
                success=False,
                error=f"Failed to download transcript ({vtt_response.status_code})",
            )
        vtt_text = vtt_response.text
        lines = vtt_text.strip().split("\n")
        transcript_lines: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped == "WEBVTT" or "-->" in stripped or stripped.isdigit():
                continue
            transcript_lines.append(stripped)
        transcript_text = "\n".join(transcript_lines)
    except httpx.TimeoutException:
        return GetMeetingTranscriptOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMeetingTranscriptOutput(success=False, error=f"Call failed: {exc}")
    return GetMeetingTranscriptOutput(
        success=True,
        transcript_url=download_url,
        transcript_text=transcript_text,
    )


@tool(args_schema=GetMeetingSummaryInput)
@serialize_pydantic_return
async def get_meeting_summary(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
) -> GetMeetingSummaryOutput:
    """Retrieve the AI-generated summary of a meeting or webinar."""
    if not auth_data.get("access_token"):
        return GetMeetingSummaryOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/meetings/{meeting_id}/meeting_summary",
                headers=headers,
            )
        if response.status_code != 200:
            return GetMeetingSummaryOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetMeetingSummaryOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetMeetingSummaryOutput(success=False, error=f"Call failed: {exc}")
    return GetMeetingSummaryOutput(
        success=True,
        summary=MeetingSummary(
            meeting_id=data.get("meeting_id"),
            meeting_uuid=data.get("meeting_uuid"),
            summary_title=data.get("summary_title"),
            summary_overview=data.get("summary_overview"),
            summary_details=data.get("summary_details"),
            next_steps=data.get("next_steps", []),
        ),
    )


@tool(args_schema=ListAllRecordingsInput)
@serialize_pydantic_return
async def list_all_recordings(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str = "me",
    from_date: str | None = None,
    to_date: str | None = None,
    trash: bool | None = None,
) -> ListAllRecordingsOutput:
    """List all cloud recordings for a user."""
    if not auth_data.get("access_token"):
        return ListAllRecordingsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if from_date is not None:
        params["from"] = from_date
    if to_date is not None:
        params["to"] = to_date
    if trash is not None:
        params["trash"] = str(trash).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/users/{user_id}/recordings",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListAllRecordingsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAllRecordingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAllRecordingsOutput(success=False, error=f"Call failed: {exc}")
    meetings = [
        RecordingMeeting(
            uuid=m.get("uuid"),
            id=m.get("id"),
            topic=m.get("topic"),
            start_time=m.get("start_time"),
            duration=m.get("duration"),
            total_size=m.get("total_size"),
            recording_count=m.get("recording_count"),
            recording_files=[
                RecordingFile(
                    id=f.get("id"),
                    meeting_id=f.get("meeting_id"),
                    recording_start=f.get("recording_start"),
                    recording_end=f.get("recording_end"),
                    file_type=f.get("file_type"),
                    file_size=f.get("file_size"),
                    download_url=f.get("download_url"),
                    play_url=f.get("play_url"),
                    status=f.get("status"),
                    recording_type=f.get("recording_type"),
                )
                for f in m.get("recording_files", [])
            ],
        )
        for m in data.get("meetings", [])
    ]
    return ListAllRecordingsOutput(
        success=True,
        meetings=meetings,
        total_records=data.get("total_records"),
    )


@tool(args_schema=ListCallRecordingsInput)
@serialize_pydantic_return
async def list_call_recordings(
    auth_type: str,
    auth_data: dict[str, Any],
    start_date: str | None = None,
    end_date: str | None = None,
) -> ListCallRecordingsOutput:
    """Get your account's Zoom Phone call recordings."""
    if not auth_data.get("access_token"):
        return ListCallRecordingsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if start_date is not None:
        params["from"] = start_date
    if end_date is not None:
        params["to"] = end_date
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/phone/recordings",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListCallRecordingsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListCallRecordingsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCallRecordingsOutput(success=False, error=f"Call failed: {exc}")
    return ListCallRecordingsOutput(
        success=True,
        recordings=data.get("recordings", []),
        total_records=data.get("total_records"),
    )


@tool(args_schema=ListUserCallLogsInput)
@serialize_pydantic_return
async def list_user_call_logs(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
) -> ListUserCallLogsOutput:
    """Get a user's Zoom Phone call logs."""
    if not auth_data.get("access_token"):
        return ListUserCallLogsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/phone/users/{user_id}/call_logs",
                headers=headers,
            )
        if response.status_code != 200:
            return ListUserCallLogsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListUserCallLogsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListUserCallLogsOutput(success=False, error=f"Call failed: {exc}")
    return ListUserCallLogsOutput(
        success=True,
        call_logs=data.get("call_logs", []),
        total_records=data.get("total_records"),
    )


@tool(args_schema=ListPastMeetingParticipantsInput)
@serialize_pydantic_return
async def list_past_meeting_participants(
    auth_type: str,
    auth_data: dict[str, Any],
    meeting_id: str,
) -> ListPastMeetingParticipantsOutput:
    """Retrieve participants from a past meeting."""
    if not auth_data.get("access_token"):
        return ListPastMeetingParticipantsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/past_meetings/{meeting_id}/participants",
                headers=headers,
            )
        if response.status_code != 200:
            return ListPastMeetingParticipantsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListPastMeetingParticipantsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPastMeetingParticipantsOutput(success=False, error=f"Call failed: {exc}")
    participants = [
        ParticipantItem(
            id=p.get("id"),
            name=p.get("name"),
            user_email=p.get("user_email"),
            join_time=p.get("join_time"),
            leave_time=p.get("leave_time"),
            duration=p.get("duration"),
        )
        for p in data.get("participants", [])
    ]
    return ListPastMeetingParticipantsOutput(
        success=True,
        participants=participants,
        total_records=data.get("total_records"),
    )


@tool(args_schema=CreateUserInput)
@serialize_pydantic_return
async def create_user(
    auth_type: str,
    auth_data: dict[str, Any],
    action: str,
    email: str,
    type: int,
    first_name: str | None = None,
    last_name: str | None = None,
) -> CreateUserOutput:
    """Create a new user in your Zoom account."""
    if not auth_data.get("access_token"):
        return CreateUserOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    user_info: dict[str, Any] = {"email": email, "type": type}
    if first_name is not None:
        user_info["first_name"] = first_name
    if last_name is not None:
        user_info["last_name"] = last_name
    body: dict[str, Any] = {"action": action, "user_info": user_info}
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/users",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateUserOutput(success=False, error=f"Call failed: {exc}")
    return CreateUserOutput(
        success=True,
        id=data.get("id"),
        email=data.get("email"),
        first_name=data.get("first_name"),
        last_name=data.get("last_name"),
        type=data.get("type"),
    )


@tool(args_schema=DeleteUserInput)
@serialize_pydantic_return
async def delete_user(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
    action: str | None = None,
    transfer_email: str | None = None,
    transfer_meeting: bool | None = None,
    transfer_webinar: bool | None = None,
    transfer_recording: bool | None = None,
) -> DeleteUserOutput:
    """Disassociate or permanently delete a user from the account."""
    if not auth_data.get("access_token"):
        return DeleteUserOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if action is not None:
        params["action"] = action
    if transfer_email is not None:
        params["transfer_email"] = transfer_email
    if transfer_meeting is not None:
        params["transfer_meeting"] = str(transfer_meeting).lower()
    if transfer_webinar is not None:
        params["transfer_webinar"] = str(transfer_webinar).lower()
    if transfer_recording is not None:
        params["transfer_recording"] = str(transfer_recording).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/users/{user_id}",
                headers=headers,
                params=params,
            )
        if response.status_code not in (200, 204):
            return DeleteUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return DeleteUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteUserOutput(success=False, error=f"Call failed: {exc}")
    return DeleteUserOutput(success=True)


@tool(args_schema=GetWebinarDetailsInput)
@serialize_pydantic_return
async def get_webinar_details(
    auth_type: str,
    auth_data: dict[str, Any],
    webinar_id: str,
    occurrence_id: str | None = None,
) -> GetWebinarDetailsOutput:
    """Get details of a scheduled webinar."""
    if not auth_data.get("access_token"):
        return GetWebinarDetailsOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if occurrence_id is not None:
        params["occurrence_id"] = occurrence_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/webinars/{webinar_id}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return GetWebinarDetailsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetWebinarDetailsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetWebinarDetailsOutput(success=False, error=f"Call failed: {exc}")
    return GetWebinarDetailsOutput(
        success=True,
        id=data.get("id"),
        uuid=data.get("uuid"),
        topic=data.get("topic"),
        type=data.get("type"),
        start_time=data.get("start_time"),
        duration=data.get("duration"),
        timezone=data.get("timezone"),
        join_url=data.get("join_url"),
        host_email=data.get("host_email"),
    )


@tool(args_schema=UpdateWebinarInput)
@serialize_pydantic_return
async def update_webinar(
    auth_type: str,
    auth_data: dict[str, Any],
    webinar_id: str,
    topic: str | None = None,
    type: int | None = None,
    start_time: str | None = None,
    duration: int | None = None,
    timezone: str | None = None,
    password: str | None = None,
    agenda: str | None = None,
) -> UpdateWebinarOutput:
    """Update a webinar's topic, start time, or other settings."""
    if not auth_data.get("access_token"):
        return UpdateWebinarOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if topic is not None:
        body["topic"] = topic
    if type is not None:
        body["type"] = type
    if start_time is not None:
        body["start_time"] = start_time
    if duration is not None:
        body["duration"] = duration
    if timezone is not None:
        body["timezone"] = timezone
    if password is not None:
        body["password"] = password
    if agenda is not None:
        body["agenda"] = agenda
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/webinars/{webinar_id}",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 204):
            return UpdateWebinarOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return UpdateWebinarOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateWebinarOutput(success=False, error=f"Call failed: {exc}")
    return UpdateWebinarOutput(success=True)


@tool(args_schema=AddWebinarRegistrantInput)
@serialize_pydantic_return
async def add_webinar_registrant(
    auth_type: str,
    auth_data: dict[str, Any],
    webinar_id: str,
    email: str,
    first_name: str,
    last_name: str,
    occurrence_ids: str | None = None,
) -> AddWebinarRegistrantOutput:
    """Register a participant for a webinar."""
    if not auth_data.get("access_token"):
        return AddWebinarRegistrantOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
    }
    params: dict[str, Any] = {}
    if occurrence_ids is not None:
        params["occurrence_ids"] = occurrence_ids
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/webinars/{webinar_id}/registrants",
                headers=headers,
                json=body,
                params=params,
            )
        if response.status_code not in (200, 201):
            return AddWebinarRegistrantOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddWebinarRegistrantOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddWebinarRegistrantOutput(success=False, error=f"Call failed: {exc}")
    return AddWebinarRegistrantOutput(
        success=True,
        registrant=RegistrantResponse(
            id=data.get("id"),
            registrant_id=data.get("registrant_id"),
            start_time=data.get("start_time"),
            join_url=data.get("join_url"),
            topic=data.get("topic"),
        ),
    )


@tool(args_schema=ListWebinarParticipantsReportInput)
@serialize_pydantic_return
async def list_webinar_participants_report(
    auth_type: str,
    auth_data: dict[str, Any],
    webinar_id: str,
) -> ListWebinarParticipantsReportOutput:
    """Retrieve detailed report on each webinar attendee. Reports available for the last 6 months."""
    if not auth_data.get("access_token"):
        return ListWebinarParticipantsReportOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/report/webinars/{webinar_id}/participants",
                headers=headers,
            )
        if response.status_code != 200:
            return ListWebinarParticipantsReportOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListWebinarParticipantsReportOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWebinarParticipantsReportOutput(success=False, error=f"Call failed: {exc}")
    participants = [
        ParticipantItem(
            id=p.get("id"),
            name=p.get("name"),
            user_email=p.get("user_email"),
            join_time=p.get("join_time"),
            leave_time=p.get("leave_time"),
            duration=p.get("duration"),
        )
        for p in data.get("participants", [])
    ]
    return ListWebinarParticipantsReportOutput(
        success=True,
        participants=participants,
        total_records=data.get("total_records"),
    )


@tool(args_schema=ListPastWebinarQaInput)
@serialize_pydantic_return
async def list_past_webinar_qa(
    auth_type: str,
    auth_data: dict[str, Any],
    webinar_id: str,
) -> ListPastWebinarQaOutput:
    """List Q&A from a past webinar."""
    if not auth_data.get("access_token"):
        return ListPastWebinarQaOutput(success=False, error="Missing or empty access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/past_webinars/{webinar_id}/qa",
                headers=headers,
            )
        if response.status_code != 200:
            return ListPastWebinarQaOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListPastWebinarQaOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListPastWebinarQaOutput(success=False, error=f"Call failed: {exc}")
    questions: list[QaItem] = []
    for q in data.get("questions", []):
        for answer in q.get("question_details", []):
            questions.append(
                QaItem(
                    question=answer.get("question"),
                    answer=answer.get("answer"),
                    name=q.get("name"),
                    email=q.get("email"),
                )
            )
    return ListPastWebinarQaOutput(
        success=True,
        questions=questions,
    )
