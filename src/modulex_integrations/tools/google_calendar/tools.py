"""Google Calendar LangChain @tool functions."""
from __future__ import annotations

import datetime
import time
import uuid
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_calendar.outputs import (
    AddAttendeesToEventOutput,
    CalendarSummary,
    ColorEntry,
    CreateEventOutput,
    DeleteEventOutput,
    EventSummary,
    FreeBusyCalendar,
    GetCalendarOutput,
    GetCurrentUserOutput,
    GetDateTimeOutput,
    GetEventOutput,
    ListCalendarsOutput,
    ListColorIdOptionsOutput,
    ListEventInstancesOutput,
    ListEventsOutput,
    QueryFreeBusyCalendarsOutput,
    QuickAddEventOutput,
    SettingItem,
    UpdateEventInstanceOutput,
    UpdateEventOutput,
    UpdateFollowingInstancesOutput,
)

__all__ = [
    "add_attendees_to_event",
    "create_event",
    "delete_event",
    "get_calendar",
    "get_current_user",
    "get_date_time",
    "get_event",
    "list_calendars",
    "list_color_id_options",
    "list_event_instances",
    "list_events",
    "query_free_busy_calendars",
    "quick_add_event",
    "update_event",
    "update_event_instance",
    "update_following_instances",
]

_BASE_URL = "https://www.googleapis.com/calendar/v3"
_TIMEOUT = 30.0

_REPEAT_FREQ_MAP: dict[str, str] = {
    "DAILY": "DAILY",
    "WEEKLY": "WEEKLY",
    "MONTHLY": "MONTHLY",
    "YEARLY": "YEARLY",
}


# --- Auth + helpers ---------------------------------------------------------


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


def _is_all_day(value: str | None) -> bool:
    if not value:
        return False
    return len(value.strip()) <= 10


def _build_date_payload(value: str | None, time_zone: str | None) -> dict[str, Any] | None:
    """Build a Google Calendar start/end object from an event date/dateTime string."""
    if not value:
        return None
    trimmed = value.strip()
    payload: dict[str, Any] = {}
    if _is_all_day(trimmed):
        payload["date"] = trimmed
    else:
        payload["dateTime"] = trimmed
    if time_zone:
        payload["timeZone"] = time_zone
    return payload


def _normalize_attendees(attendees: list[str] | None) -> list[dict[str, str]]:
    if not attendees:
        return []
    out: list[dict[str, str]] = []
    for entry in attendees:
        if not isinstance(entry, str):
            continue
        email = entry.strip()
        if email:
            out.append({"email": email})
    return out


def _format_recurrence(
    repeat_frequency: str | None,
    repeat_interval: int | None,
    repeat_times: int | None,
    repeat_until: str | None,
    repeat_specific_days: list[str] | None = None,
) -> list[str] | None:
    if not repeat_frequency:
        return None
    freq = _REPEAT_FREQ_MAP.get(repeat_frequency.upper())
    if not freq:
        return None
    parts = [f"FREQ={freq}"]
    interval = repeat_interval or 1
    parts.append(f"INTERVAL={interval}")
    if freq == "WEEKLY" and repeat_specific_days:
        parts.append("BYDAY=" + ",".join(repeat_specific_days))
    if repeat_until:
        only_date = repeat_until.replace("-", "")
        parts.append(f"UNTIL={only_date}T235959Z")
    elif repeat_times:
        parts.append(f"COUNT={repeat_times}")
    return ["RRULE:" + ";".join(parts)]


def _drop_none(d: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def _build_query_params(items: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {}
    for key, val in items.items():
        if val is None:
            continue
        if isinstance(val, bool):
            params[key] = "true" if val else "false"
        elif isinstance(val, list):
            if val:
                params[key] = val
        else:
            params[key] = val
    return params


# --- Input schemas ----------------------------------------------------------


class AddAttendeesToEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    event_id: str = Field(description="ID of the event to update.")
    attendees: list[str] = Field(description="List of attendee email addresses to add (existing attendees are preserved).")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    send_updates: str | None = Field(default=None, description="Whether to send notifications: all, externalOnly, none.")


class CreateEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    summary: str = Field(description="Event title.")
    event_start_date: str = Field(description="Event start (yyyy-mm-dd or RFC3339).")
    event_end_date: str = Field(description="Event end (yyyy-mm-dd or RFC3339).")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    location: str | None = Field(default=None, description="Event location.")
    description: str | None = Field(default=None, description="Event description.")
    attendees: list[str] | None = Field(default=None, description="List of attendee email addresses.")
    color_id: str | None = Field(default=None, description="Color ID for the event.")
    time_zone: str | None = Field(default=None, description="IANA time zone.")
    send_updates: str | None = Field(default=None, description="Whether to send invitations.")
    create_meet_room: bool = Field(default=False, description="Attach a Google Meet conference link.")
    visibility: str | None = Field(default=None, description="Event visibility.")
    repeat_frequency: str | None = Field(default=None, description="Recurrence frequency.")
    repeat_interval: int | None = Field(default=None, description="Recurrence interval.")
    repeat_specific_days: list[str] | None = Field(default=None, description="Two-letter weekday codes.")
    repeat_until: str | None = Field(default=None, description="Recurrence end date.")
    repeat_times: int | None = Field(default=None, description="Recurrence occurrence count.")


class DeleteEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    event_id: str = Field(description="ID of the event to delete.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    send_updates: str | None = Field(default=None, description="Whether to send cancellation notifications.")


class GetCalendarInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")


class GetCurrentUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


class GetDateTimeInput(BaseModel):
    auth_type: str = Field(description="Authentication type (ignored — computed locally).")
    auth_data: dict[str, Any] = Field(description="Authentication data (ignored — computed locally).")


class GetEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    event_id: str = Field(description="ID of the event to retrieve.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")


class ListCalendarsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


class ListColorIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


class ListEventInstancesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    event_id: str = Field(description="ID of the recurring event.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    max_attendees: int | None = Field(default=None, description="Maximum attendees per instance.")
    max_results: int | None = Field(default=None, description="Maximum number of instances to return.")
    show_deleted: bool | None = Field(default=None, description="Include cancelled instances.")
    time_min: str | None = Field(default=None, description="Lower bound (RFC3339).")
    time_max: str | None = Field(default=None, description="Upper bound (RFC3339).")
    time_zone: str | None = Field(default=None, description="IANA time zone for the response.")


class ListEventsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    i_cal_uid: str | None = Field(default=None, description="Filter by iCalendar UID.")
    max_attendees: int | None = Field(default=None, description="Maximum attendees per event.")
    max_results: int | None = Field(default=None, description="Maximum number of events to return.")
    order_by: str | None = Field(default=None, description="Sort order: startTime, updated.")
    private_extended_property: str | None = Field(default=None, description="propertyName=value constraint on private properties.")
    q: str | None = Field(default=None, description="Free-text search.")
    shared_extended_property: str | None = Field(default=None, description="propertyName=value constraint on shared properties.")
    show_deleted: bool | None = Field(default=None, description="Include cancelled events.")
    show_hidden_invitations: bool | None = Field(default=None, description="Include hidden invitations.")
    single_events: bool | None = Field(default=None, description="Expand recurring events into instances.")
    time_max: str | None = Field(default=None, description="Upper bound (RFC3339).")
    time_min: str | None = Field(default=None, description="Lower bound (RFC3339).")
    time_zone: str | None = Field(default=None, description="IANA time zone for the response.")
    updated_min: str | None = Field(default=None, description="Lower bound for last-modified time (RFC3339).")
    event_types: list[str] | None = Field(default=None, description="Filter by event type.")


class QueryFreeBusyCalendarsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    time_min: str = Field(description="Start of the query window (RFC3339).")
    time_max: str = Field(description="End of the query window (RFC3339).")
    calendar_ids: list[str] = Field(default_factory=lambda: ["primary"], description="List of calendar IDs to query.")
    time_zone: str | None = Field(default=None, description="IANA time zone for the response.")


class QuickAddEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    text: str = Field(description="Natural-language event description.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    attendees: list[str] | None = Field(default=None, description="Optional list of attendee email addresses.")


class UpdateEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    event_id: str = Field(description="ID of the event to update.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    summary: str | None = Field(default=None, description="New event title.")
    event_start_date: str | None = Field(default=None, description="New start.")
    event_end_date: str | None = Field(default=None, description="New end.")
    location: str | None = Field(default=None, description="New event location.")
    description: str | None = Field(default=None, description="New event description.")
    attendees: list[str] | None = Field(default=None, description="Replacement list of attendee email addresses.")
    color_id: str | None = Field(default=None, description="New color ID.")
    time_zone: str | None = Field(default=None, description="IANA time zone.")
    send_updates: str | None = Field(default=None, description="Whether to send notifications.")
    repeat_frequency: str | None = Field(default=None, description="Updated recurrence frequency.")
    repeat_interval: int | None = Field(default=None, description="Updated recurrence interval.")
    repeat_specific_days: list[str] | None = Field(default=None, description="Two-letter weekday codes.")
    repeat_until: str | None = Field(default=None, description="New recurrence end date.")
    repeat_times: int | None = Field(default=None, description="New occurrence count.")


class UpdateEventInstanceInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    instance_id: str = Field(description="ID of the recurring-event instance to update.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    summary: str | None = Field(default=None, description="New event title.")
    event_start_date: str | None = Field(default=None, description="New start.")
    event_end_date: str | None = Field(default=None, description="New end.")
    location: str | None = Field(default=None, description="New event location.")
    description: str | None = Field(default=None, description="New event description.")
    attendees: list[str] | None = Field(default=None, description="Replacement list of attendee email addresses.")
    color_id: str | None = Field(default=None, description="New color ID.")
    time_zone: str | None = Field(default=None, description="IANA time zone.")
    send_updates: str | None = Field(default=None, description="Whether to send notifications.")


class UpdateFollowingInstancesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    recurring_event_id: str = Field(description="ID of the parent recurring event.")
    instance_id: str = Field(description="ID of the instance from which the split begins.")
    calendar_id: str = Field(default="primary", description="Calendar identifier.")
    summary: str | None = Field(default=None, description="New event title for the split series.")
    event_start_date: str | None = Field(default=None, description="New start for the split series.")
    event_end_date: str | None = Field(default=None, description="New end for the split series.")
    location: str | None = Field(default=None, description="New location for the split series.")
    description: str | None = Field(default=None, description="New description for the split series.")
    attendees: list[str] | None = Field(default=None, description="Replacement list of attendee email addresses.")
    color_id: str | None = Field(default=None, description="New color ID for the split series.")
    time_zone: str | None = Field(default=None, description="IANA time zone.")
    send_updates: str | None = Field(default=None, description="Whether to send notifications.")
    repeat_frequency: str | None = Field(default=None, description="Optional new recurrence frequency.")
    repeat_interval: int | None = Field(default=None, description="Optional new recurrence interval.")
    repeat_until: str | None = Field(default=None, description="Optional new recurrence end date.")
    repeat_times: int | None = Field(default=None, description="Optional new occurrence count.")


# --- @tool functions --------------------------------------------------------


@tool(args_schema=AddAttendeesToEventInput)
@serialize_pydantic_return
async def add_attendees_to_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    attendees: list[str],
    calendar_id: str = "primary",
    send_updates: str | None = None,
) -> AddAttendeesToEventOutput:
    """Add attendees to an existing Google Calendar event."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        get_resp = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
        )
        get_resp.raise_for_status()
        current_event = get_resp.json()

        new_attendees = _normalize_attendees(attendees)
        existing_attendees = current_event.get("attendees") or []
        merged: list[dict[str, Any]] = list(new_attendees)
        merged.extend(existing_attendees)

        body = dict(current_event)
        body["attendees"] = merged

        params = _build_query_params({"sendUpdates": send_updates})
        put_resp = await client.put(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
            params=params,
            json=body,
        )
        put_resp.raise_for_status()
        updated = put_resp.json()
    return AddAttendeesToEventOutput(
        success=True,
        event=EventSummary.model_validate(updated),
    )


@tool(args_schema=CreateEventInput)
@serialize_pydantic_return
async def create_event(
    auth_type: str,
    auth_data: dict[str, Any],
    summary: str,
    event_start_date: str,
    event_end_date: str,
    calendar_id: str = "primary",
    location: str | None = None,
    description: str | None = None,
    attendees: list[str] | None = None,
    color_id: str | None = None,
    time_zone: str | None = None,
    send_updates: str | None = None,
    create_meet_room: bool = False,
    visibility: str | None = None,
    repeat_frequency: str | None = None,
    repeat_interval: int | None = None,
    repeat_specific_days: list[str] | None = None,
    repeat_until: str | None = None,
    repeat_times: int | None = None,
) -> CreateEventOutput:
    """Create a new event in a Google Calendar."""
    headers = _get_auth_headers(auth_type, auth_data)

    body: dict[str, Any] = _drop_none({
        "summary": summary,
        "location": location,
        "description": description,
        "start": _build_date_payload(event_start_date, time_zone),
        "end": _build_date_payload(event_end_date, time_zone),
        "recurrence": _format_recurrence(
            repeat_frequency,
            repeat_interval,
            repeat_times,
            repeat_until,
            repeat_specific_days,
        ),
        "attendees": _normalize_attendees(attendees) or None,
        "colorId": color_id,
        "visibility": visibility,
    })

    params: dict[str, Any] = _build_query_params({"sendUpdates": send_updates})
    if create_meet_room:
        params["conferenceDataVersion"] = 1
        body["conferenceData"] = {
            "createRequest": {
                "requestId": str(uuid.uuid4()),
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            },
        }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(
            f"{_BASE_URL}/calendars/{calendar_id}/events",
            headers=headers,
            params=params,
            json=body,
        )
        response.raise_for_status()
        event = response.json()
    return CreateEventOutput(
        success=True,
        event=EventSummary.model_validate(event),
    )


@tool(args_schema=DeleteEventInput)
@serialize_pydantic_return
async def delete_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    calendar_id: str = "primary",
    send_updates: str | None = None,
) -> DeleteEventOutput:
    """Delete an event from a Google Calendar."""
    headers = _get_auth_headers(auth_type, auth_data)
    params = _build_query_params({"sendUpdates": send_updates})
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.delete(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
    return DeleteEventOutput(
        success=True,
        eventId=event_id,
        statusCode=response.status_code,
    )


@tool(args_schema=GetCalendarInput)
@serialize_pydantic_return
async def get_calendar(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str = "primary",
) -> GetCalendarOutput:
    """Retrieve metadata for a Google Calendar."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetCalendarOutput(
        success=True,
        calendar=CalendarSummary.model_validate(data),
    )


@tool(args_schema=GetCurrentUserInput)
@serialize_pydantic_return
async def get_current_user(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCurrentUserOutput:
    """Retrieve the authenticated user's primary calendar, calendar list, settings, and color palette."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        primary_resp = await client.get(
            f"{_BASE_URL}/calendars/primary",
            headers=headers,
        )
        primary_resp.raise_for_status()
        primary = primary_resp.json()

        list_resp = await client.get(
            f"{_BASE_URL}/users/me/calendarList",
            headers=headers,
            params={"maxResults": 25},
        )
        list_resp.raise_for_status()
        calendar_list = list_resp.json()

        settings_resp = await client.get(
            f"{_BASE_URL}/users/me/settings",
            headers=headers,
        )
        settings_resp.raise_for_status()
        settings_payload = settings_resp.json()

        colors_resp = await client.get(
            f"{_BASE_URL}/colors",
            headers=headers,
        )
        colors_resp.raise_for_status()
        colors_payload = colors_resp.json()

    settings_items = settings_payload.get("items") or []
    timezone_setting = next(
        (item.get("value") for item in settings_items if item.get("id") == "timezone"),
        None,
    )
    locale_setting = next(
        (item.get("value") for item in settings_items if item.get("id") == "locale"),
        None,
    )

    return GetCurrentUserOutput(
        success=True,
        primaryCalendar=CalendarSummary.model_validate(primary),
        calendars=[CalendarSummary.model_validate(c) for c in (calendar_list.get("items") or [])],
        settings=[SettingItem.model_validate(s) for s in settings_items],
        timezone=timezone_setting or primary.get("timeZone"),
        locale=locale_setting,
        colors=colors_payload,
    )


@tool(args_schema=GetDateTimeInput)
@serialize_pydantic_return
async def get_date_time(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetDateTimeOutput:
    """Return the current date/time, IANA timezone, UTC offset, ISO string, and RFC3339 timestamp."""
    now_local = datetime.datetime.now().astimezone()
    date_part = now_local.strftime("%Y-%m-%d")
    time_part = now_local.strftime("%H:%M:%S")
    tzinfo = now_local.tzinfo
    timezone_name = str(tzinfo) if tzinfo is not None else "UTC"
    offset_td = tzinfo.utcoffset(now_local) if tzinfo is not None else datetime.timedelta(0)
    total_minutes = int((offset_td or datetime.timedelta(0)).total_seconds() // 60)
    sign = "+" if total_minutes >= 0 else "-"
    abs_minutes = abs(total_minutes)
    offset_str = f"{sign}{abs_minutes // 60:02d}:{abs_minutes % 60:02d}"
    timestamp_ms = int(time.time() * 1000)
    iso_string = now_local.astimezone(datetime.UTC).isoformat().replace("+00:00", "Z")
    rfc3339 = f"{date_part}T{time_part}{offset_str}"

    return GetDateTimeOutput(
        success=True,
        date=date_part,
        time=time_part,
        timezone=timezone_name,
        timezoneOffset=offset_str,
        timestamp=timestamp_ms,
        isoString=iso_string,
        rfc3339=rfc3339,
    )


@tool(args_schema=GetEventInput)
@serialize_pydantic_return
async def get_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    calendar_id: str = "primary",
) -> GetEventOutput:
    """Retrieve a single event from a Google Calendar."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetEventOutput(
        success=True,
        event=EventSummary.model_validate(data),
    )


@tool(args_schema=ListCalendarsInput)
@serialize_pydantic_return
async def list_calendars(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListCalendarsOutput:
    """List calendars the authenticated user can access."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_BASE_URL}/users/me/calendarList",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    items = data.get("items") or []
    return ListCalendarsOutput(
        success=True,
        calendars=[CalendarSummary.model_validate(c) for c in items],
    )


@tool(args_schema=ListColorIdOptionsInput)
@serialize_pydantic_return
async def list_color_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListColorIdOptionsOutput:
    """List available color ID options for events, with hex backgrounds."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.get(
            f"{_BASE_URL}/colors",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    event_colors = (data.get("event") or {})
    options = [
        ColorEntry(label=str(value.get("background") or key), value=str(key))
        for key, value in event_colors.items()
    ]
    return ListColorIdOptionsOutput(success=True, options=options)


@tool(args_schema=ListEventInstancesInput)
@serialize_pydantic_return
async def list_event_instances(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    calendar_id: str = "primary",
    max_attendees: int | None = None,
    max_results: int | None = None,
    show_deleted: bool | None = None,
    time_min: str | None = None,
    time_max: str | None = None,
    time_zone: str | None = None,
) -> ListEventInstancesOutput:
    """List individual instances of a recurring event."""
    headers = _get_auth_headers(auth_type, auth_data)
    base_params = _build_query_params({
        "maxAttendees": max_attendees,
        "showDeleted": show_deleted,
        "timeMin": time_min,
        "timeMax": time_max,
        "timeZone": time_zone,
    })

    instances: list[dict[str, Any]] = []
    page_token: str | None = None
    max_pages = 50
    pages_seen = 0
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        while pages_seen < max_pages:
            pages_seen += 1
            params = dict(base_params)
            if page_token:
                params["pageToken"] = page_token
            response = await client.get(
                f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}/instances",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            instances.extend(data.get("items") or [])
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            if max_results and len(instances) >= max_results:
                break
    if max_results and len(instances) > max_results:
        instances = instances[:max_results]
    return ListEventInstancesOutput(
        success=True,
        instances=[EventSummary.model_validate(i) for i in instances],
    )


@tool(args_schema=ListEventsInput)
@serialize_pydantic_return
async def list_events(
    auth_type: str,
    auth_data: dict[str, Any],
    calendar_id: str = "primary",
    i_cal_uid: str | None = None,
    max_attendees: int | None = None,
    max_results: int | None = None,
    order_by: str | None = None,
    private_extended_property: str | None = None,
    q: str | None = None,
    shared_extended_property: str | None = None,
    show_deleted: bool | None = None,
    show_hidden_invitations: bool | None = None,
    single_events: bool | None = None,
    time_max: str | None = None,
    time_min: str | None = None,
    time_zone: str | None = None,
    updated_min: str | None = None,
    event_types: list[str] | None = None,
) -> ListEventsOutput:
    """List events on a Google Calendar, with optional filters and pagination."""
    if order_by == "startTime" and not single_events:
        return ListEventsOutput(success=False, events=[])
    headers = _get_auth_headers(auth_type, auth_data)
    base_params = _build_query_params({
        "iCalUID": i_cal_uid,
        "maxAttendees": max_attendees,
        "orderBy": order_by,
        "privateExtendedProperty": private_extended_property,
        "q": q,
        "sharedExtendedProperty": shared_extended_property,
        "showDeleted": show_deleted,
        "showHiddenInvitations": show_hidden_invitations,
        "singleEvents": single_events,
        "timeMax": time_max,
        "timeMin": time_min,
        "timeZone": time_zone,
        "updatedMin": updated_min,
        "eventTypes": event_types,
    })

    events: list[dict[str, Any]] = []
    page_token: str | None = None
    max_pages = 50
    pages_seen = 0
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        while pages_seen < max_pages:
            pages_seen += 1
            params = dict(base_params)
            if page_token:
                params["pageToken"] = page_token
            response = await client.get(
                f"{_BASE_URL}/calendars/{calendar_id}/events",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            events.extend(data.get("items") or [])
            page_token = data.get("nextPageToken")
            if not page_token:
                break
            if max_results and len(events) >= max_results:
                break
    if max_results and len(events) > max_results:
        events = events[:max_results]
    for ev in events:
        if not ev.get("summary"):
            ev["summary"] = f"Event ID: {ev.get('id', '')}"
    return ListEventsOutput(
        success=True,
        events=[EventSummary.model_validate(e) for e in events],
    )


@tool(args_schema=QueryFreeBusyCalendarsInput)
@serialize_pydantic_return
async def query_free_busy_calendars(
    auth_type: str,
    auth_data: dict[str, Any],
    time_min: str,
    time_max: str,
    calendar_ids: list[str] | None = None,
    time_zone: str | None = None,
) -> QueryFreeBusyCalendarsOutput:
    """Query free/busy time blocks across one or more calendars over a date range."""
    headers = _get_auth_headers(auth_type, auth_data)
    ids = calendar_ids or ["primary"]
    body = _drop_none({
        "timeMin": time_min,
        "timeMax": time_max,
        "timeZone": time_zone,
        "items": [{"id": cid} for cid in ids],
    })
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(
            f"{_BASE_URL}/freeBusy",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    raw_calendars = data.get("calendars") or {}
    calendars_out = {
        cid: FreeBusyCalendar.model_validate(entry)
        for cid, entry in raw_calendars.items()
    }
    return QueryFreeBusyCalendarsOutput(
        success=True,
        timeMin=data.get("timeMin") or time_min,
        timeMax=data.get("timeMax") or time_max,
        calendars=calendars_out,
    )


@tool(args_schema=QuickAddEventInput)
@serialize_pydantic_return
async def quick_add_event(
    auth_type: str,
    auth_data: dict[str, Any],
    text: str,
    calendar_id: str = "primary",
    attendees: list[str] | None = None,
) -> QuickAddEventOutput:
    """Create an event from a natural-language string (Google parses date/time/title)."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        quick_resp = await client.post(
            f"{_BASE_URL}/calendars/{calendar_id}/events/quickAdd",
            headers=headers,
            params={"text": text},
        )
        quick_resp.raise_for_status()
        event = quick_resp.json()

        if attendees:
            attendees_payload = _normalize_attendees(attendees)
            body = dict(event)
            body["attendees"] = attendees_payload
            update_resp = await client.put(
                f"{_BASE_URL}/calendars/{calendar_id}/events/{event['id']}",
                headers=headers,
                json=body,
            )
            update_resp.raise_for_status()
            event = update_resp.json()
    return QuickAddEventOutput(
        success=True,
        event=EventSummary.model_validate(event),
    )


@tool(args_schema=UpdateEventInput)
@serialize_pydantic_return
async def update_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    event_start_date: str | None = None,
    event_end_date: str | None = None,
    location: str | None = None,
    description: str | None = None,
    attendees: list[str] | None = None,
    color_id: str | None = None,
    time_zone: str | None = None,
    send_updates: str | None = None,
    repeat_frequency: str | None = None,
    repeat_interval: int | None = None,
    repeat_specific_days: list[str] | None = None,
    repeat_until: str | None = None,
    repeat_times: int | None = None,
) -> UpdateEventOutput:
    """Update an existing event on a Google Calendar."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        get_resp = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
        )
        get_resp.raise_for_status()
        current = get_resp.json()

        current_start_tz = (current.get("start") or {}).get("timeZone")
        current_end_tz = (current.get("end") or {}).get("timeZone")
        effective_tz = time_zone or current_start_tz

        body: dict[str, Any] = {
            "summary": summary if summary is not None else current.get("summary"),
            "location": location if location is not None else current.get("location"),
            "description": description if description is not None else current.get("description"),
            "start": _build_date_payload(
                event_start_date
                or (current.get("start") or {}).get("dateTime")
                or (current.get("start") or {}).get("date"),
                effective_tz,
            ),
            "end": _build_date_payload(
                event_end_date
                or (current.get("end") or {}).get("dateTime")
                or (current.get("end") or {}).get("date"),
                time_zone or current_end_tz,
            ),
        }
        recurrence = _format_recurrence(
            repeat_frequency,
            repeat_interval,
            repeat_times,
            repeat_until,
            repeat_specific_days,
        )
        if recurrence is not None:
            body["recurrence"] = recurrence
        elif current.get("recurrence"):
            body["recurrence"] = current.get("recurrence")
        if attendees is not None:
            body["attendees"] = _normalize_attendees(attendees)
        elif current.get("attendees"):
            body["attendees"] = current.get("attendees")
        body = _drop_none(body)

        params = _build_query_params({"sendUpdates": send_updates})
        response = await client.put(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{event_id}",
            headers=headers,
            params=params,
            json=body,
        )
        response.raise_for_status()
        updated = response.json()
    return UpdateEventOutput(
        success=True,
        event=EventSummary.model_validate(updated),
    )


@tool(args_schema=UpdateEventInstanceInput)
@serialize_pydantic_return
async def update_event_instance(
    auth_type: str,
    auth_data: dict[str, Any],
    instance_id: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    event_start_date: str | None = None,
    event_end_date: str | None = None,
    location: str | None = None,
    description: str | None = None,
    attendees: list[str] | None = None,
    color_id: str | None = None,
    time_zone: str | None = None,
    send_updates: str | None = None,
) -> UpdateEventInstanceOutput:
    """Update a single instance of a recurring event (changes apply only to that instance)."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        get_resp = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{instance_id}",
            headers=headers,
        )
        get_resp.raise_for_status()
        current = get_resp.json()

        current_start_tz = (current.get("start") or {}).get("timeZone")
        current_end_tz = (current.get("end") or {}).get("timeZone")
        effective_tz = time_zone or current_start_tz

        body: dict[str, Any] = {
            "summary": summary if summary is not None else current.get("summary"),
            "location": location if location is not None else current.get("location"),
            "description": description if description is not None else current.get("description"),
            "start": _build_date_payload(
                event_start_date
                or (current.get("start") or {}).get("dateTime")
                or (current.get("start") or {}).get("date"),
                effective_tz,
            ),
            "end": _build_date_payload(
                event_end_date
                or (current.get("end") or {}).get("dateTime")
                or (current.get("end") or {}).get("date"),
                time_zone or current_end_tz,
            ),
            "colorId": color_id if color_id is not None else current.get("colorId"),
        }
        if attendees is not None:
            body["attendees"] = _normalize_attendees(attendees)
        elif current.get("attendees"):
            body["attendees"] = current.get("attendees")
        body = _drop_none(body)

        params = _build_query_params({"sendUpdates": send_updates})
        response = await client.put(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{instance_id}",
            headers=headers,
            params=params,
            json=body,
        )
        response.raise_for_status()
        updated = response.json()
    return UpdateEventInstanceOutput(
        success=True,
        event=EventSummary.model_validate(updated),
    )


def _calculate_until_date(instance_start: str) -> str:
    """Compute an RRULE UNTIL=YYYYMMDDTHHMMSSZ value one second before instance_start."""
    raw = instance_start
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.datetime.fromisoformat(raw)
    except ValueError:
        # Fall back to date-only parsing.
        parsed = datetime.datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=datetime.UTC)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=datetime.UTC)
    target = parsed.astimezone(datetime.UTC) - datetime.timedelta(seconds=1)
    return target.strftime("%Y%m%dT%H%M%SZ")


def _modify_recurrence_rule(rules: list[str] | None, until: str) -> list[str] | None:
    if not rules:
        return rules
    out: list[str] = []
    for rule in rules:
        if not rule.startswith("RRULE:"):
            out.append(rule)
            continue
        # strip existing UNTIL/COUNT
        cleaned = []
        for token in rule[len("RRULE:"):].split(";"):
            if token.startswith("UNTIL=") or token.startswith("COUNT="):
                continue
            cleaned.append(token)
        cleaned.append(f"UNTIL={until}")
        out.append("RRULE:" + ";".join(cleaned))
    return out


def _strip_count(rules: list[str] | None) -> list[str] | None:
    if not rules:
        return rules
    out: list[str] = []
    for rule in rules:
        if not rule.startswith("RRULE:"):
            out.append(rule)
            continue
        cleaned = [t for t in rule[len("RRULE:"):].split(";") if not t.startswith("COUNT=")]
        out.append("RRULE:" + ";".join(cleaned))
    return out


@tool(args_schema=UpdateFollowingInstancesInput)
@serialize_pydantic_return
async def update_following_instances(
    auth_type: str,
    auth_data: dict[str, Any],
    recurring_event_id: str,
    instance_id: str,
    calendar_id: str = "primary",
    summary: str | None = None,
    event_start_date: str | None = None,
    event_end_date: str | None = None,
    location: str | None = None,
    description: str | None = None,
    attendees: list[str] | None = None,
    color_id: str | None = None,
    time_zone: str | None = None,
    send_updates: str | None = None,
    repeat_frequency: str | None = None,
    repeat_interval: int | None = None,
    repeat_until: str | None = None,
    repeat_times: int | None = None,
) -> UpdateFollowingInstancesOutput:
    """Update all instances of a recurring event from a given instance forward by splitting the series."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        # Step 1: get the original recurring event
        orig_resp = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{recurring_event_id}",
            headers=headers,
        )
        orig_resp.raise_for_status()
        original_event = orig_resp.json()

        # Step 2: get the target instance
        inst_resp = await client.get(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{instance_id}",
            headers=headers,
        )
        inst_resp.raise_for_status()
        target_instance = inst_resp.json()

        start_block = target_instance.get("start") or {}
        instance_start = start_block.get("dateTime") or start_block.get("date") or ""
        until_token = _calculate_until_date(instance_start)

        # Step 3: delete the target instance while it is still part of the series
        delete_params = _build_query_params({"sendUpdates": send_updates})
        del_resp = await client.delete(
            f"{_BASE_URL}/calendars/{calendar_id}/events/{instance_id}",
            headers=headers,
            params=delete_params,
        )
        del_resp.raise_for_status()

        step4_trim_applied = False
        try:
            # Step 4: trim the original event's recurrence with UNTIL
            trimmed_recurrence = _modify_recurrence_rule(
                original_event.get("recurrence"),
                until_token,
            )
            trim_body = dict(original_event)
            if trimmed_recurrence is not None:
                trim_body["recurrence"] = trimmed_recurrence
            trim_resp = await client.put(
                f"{_BASE_URL}/calendars/{calendar_id}/events/{recurring_event_id}",
                headers=headers,
                params=delete_params,
                json=trim_body,
            )
            trim_resp.raise_for_status()
            step4_trim_applied = True

            # Step 5: create new recurring event picking up from the target instance
            effective_tz = time_zone or (start_block.get("timeZone"))
            end_block = target_instance.get("end") or {}

            if repeat_frequency:
                new_recurrence = _format_recurrence(
                    repeat_frequency,
                    repeat_interval,
                    repeat_times,
                    repeat_until,
                    None,
                )
            else:
                new_recurrence = _strip_count(original_event.get("recurrence"))

            new_body: dict[str, Any] = _drop_none({
                "summary": summary or original_event.get("summary"),
                "location": location or original_event.get("location"),
                "description": description or original_event.get("description"),
                "start": _build_date_payload(
                    event_start_date or instance_start,
                    effective_tz,
                ),
                "end": _build_date_payload(
                    event_end_date
                    or end_block.get("dateTime")
                    or end_block.get("date"),
                    time_zone or end_block.get("timeZone"),
                ),
                "recurrence": new_recurrence,
                "attendees": (
                    _normalize_attendees(attendees)
                    if attendees is not None
                    else original_event.get("attendees")
                ),
                "colorId": color_id or original_event.get("colorId"),
            })

            create_resp = await client.post(
                f"{_BASE_URL}/calendars/{calendar_id}/events",
                headers=headers,
                params=delete_params,
                json=new_body,
            )
            create_resp.raise_for_status()
            new_event = create_resp.json()
        except Exception:
            # Attempt to restore the deleted instance by patching status back to confirmed.
            restore_body = dict(target_instance)
            restore_body["status"] = "confirmed"
            try:
                await client.put(
                    f"{_BASE_URL}/calendars/{calendar_id}/events/{instance_id}",
                    headers=headers,
                    params=delete_params,
                    json=restore_body,
                )
            except Exception:
                pass
            # Surface a partial-failure marker but re-raise so the runtime sees it.
            _ = step4_trim_applied
            raise

    return UpdateFollowingInstancesOutput(
        success=True,
        originalEventId=recurring_event_id,
        newEvent=EventSummary.model_validate(new_event),
        trimmedRecurrence=trimmed_recurrence,
    )
