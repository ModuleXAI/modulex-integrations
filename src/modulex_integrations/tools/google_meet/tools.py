"""Google Meet LangChain @tool functions."""
from __future__ import annotations

import uuid
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_meet.outputs import (
    ColorIdOption,
    ListColorIdOptionsOutput,
    ScheduleMeetingOutput,
)

__all__ = [
    "list_color_id_options",
    "schedule_meeting",
]

_BASE_URL = "https://www.googleapis.com/calendar/v3"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Calendar API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _format_date_param(value: str, time_zone: str | None) -> dict[str, Any]:
    """Map a yyyy-mm-dd or RFC3339 string into Google's start/end shape."""
    out: dict[str, Any] = {}
    if value and len(value) <= 10:
        out["date"] = value
    elif value:
        out["dateTime"] = value
    if time_zone:
        out["timeZone"] = time_zone
    return out


# --- Input schemas --------------------------------------------------------


class ScheduleMeetingInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    event_start_date: str = Field(
        description=(
            "For all-day events use yyyy-mm-dd. For timed events use RFC3339 "
            "(yyyy-mm-ddThh:mm:ss+01:00)."
        ),
    )
    event_end_date: str = Field(
        description=(
            "For all-day events use yyyy-mm-dd. For timed events use RFC3339 "
            "(yyyy-mm-ddThh:mm:ss+01:00)."
        ),
    )
    calendar_id: str = Field(
        default="primary",
        description="Calendar ID. Defaults to 'primary'.",
    )
    summary: str | None = Field(default=None, description="Event title.")
    location: str | None = Field(default=None, description="Event location.")
    description: str | None = Field(default=None, description="Event description.")
    attendees: list[str] | None = Field(
        default=None,
        description="List of attendee email addresses.",
    )
    recurrence: list[str] | None = Field(
        default=None,
        description="RRULE strings describing recurrence.",
    )
    time_zone: str | None = Field(
        default=None,
        description="IANA time zone name (e.g. 'America/Los_Angeles').",
    )
    send_updates: str | None = Field(
        default=None,
        description="Who to notify: 'all', 'externalOnly', or 'none'.",
    )
    send_notifications: bool | None = Field(
        default=None,
        description="Whether to send notifications about the event update.",
    )
    color_id: str | None = Field(
        default=None,
        description="Color ID for the event (see list_color_id_options).",
    )


class ListColorIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ScheduleMeetingInput)
@serialize_pydantic_return
async def schedule_meeting(
    auth_type: str,
    auth_data: dict[str, Any],
    event_start_date: str,
    event_end_date: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    location: str | None = None,
    description: str | None = None,
    attendees: list[str] | None = None,
    recurrence: list[str] | None = None,
    time_zone: str | None = None,
    send_updates: str | None = None,
    send_notifications: bool | None = None,
    color_id: str | None = None,
) -> ScheduleMeetingOutput:
    """Creates a new event in Google Calendar with a Google Meet link attached."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return ScheduleMeetingOutput(
            success=False,
            error="Missing OAuth access_token in auth_data.",
        )

    resource: dict[str, Any] = {
        "start": _format_date_param(event_start_date, time_zone),
        "end": _format_date_param(event_end_date, time_zone),
        "conferenceData": {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            },
        },
    }
    if summary is not None:
        resource["summary"] = summary
    if location is not None:
        resource["location"] = location
    if description is not None:
        resource["description"] = description
    if recurrence is not None:
        resource["recurrence"] = recurrence
    if attendees:
        resource["attendees"] = [{"email": email} for email in attendees]
    if color_id is not None:
        resource["colorId"] = color_id

    params: dict[str, Any] = {"conferenceDataVersion": 1}
    if send_updates is not None:
        params["sendUpdates"] = send_updates
    if send_notifications is not None:
        params["sendNotifications"] = "true" if send_notifications else "false"

    url = f"{_BASE_URL}/calendars/{calendar_id}/events"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                json=resource,
            )
        if response.status_code not in (200, 201):
            return ScheduleMeetingOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ScheduleMeetingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ScheduleMeetingOutput(success=False, error=f"Call failed: {exc}")

    conference_data = data.get("conferenceData") or {}
    meet_link: str | None = None
    for entry_point in conference_data.get("entryPoints") or []:
        if entry_point.get("entryPointType") == "video":
            meet_link = entry_point.get("uri")
            break

    return ScheduleMeetingOutput(
        success=True,
        event_id=data.get("id"),
        html_link=data.get("htmlLink"),
        hangout_link=data.get("hangoutLink"),
        meet_link=meet_link,
        status=data.get("status"),
        summary=data.get("summary"),
        start=data.get("start"),
        end=data.get("end"),
        attendees=data.get("attendees") or [],
        conference_data=conference_data or None,
        event=data,
    )


@tool(args_schema=ListColorIdOptionsInput)
@serialize_pydantic_return
async def list_color_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListColorIdOptionsOutput:
    """Retrieves the available event color options from Google Calendar."""
    headers = _get_auth_headers(auth_type, auth_data)
    if "Authorization" not in headers:
        return ListColorIdOptionsOutput(
            success=False,
            error="Missing OAuth access_token in auth_data.",
        )

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/colors", headers=headers)
        if response.status_code != 200:
            return ListColorIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListColorIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListColorIdOptionsOutput(success=False, error=f"Call failed: {exc}")

    event_colors = (data.get("event") or {}) if isinstance(data, dict) else {}
    options = [
        ColorIdOption(
            id=key,
            background=(value or {}).get("background") if isinstance(value, dict) else None,
            foreground=(value or {}).get("foreground") if isinstance(value, dict) else None,
        )
        for key, value in event_colors.items()
    ]

    return ListColorIdOptionsOutput(
        success=True,
        options=options,
        count=len(options),
    )
