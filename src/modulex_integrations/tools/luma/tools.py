"""Luma LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.luma.outputs import (
    AddGuestsOutput,
    CreateEventOutput,
    GetEventOutput,
    GetGuestOutput,
    GetGuestsOutput,
    ListEventsOutput,
    ListTicketTypesOutput,
    SendInvitesOutput,
)

__all__ = [
    "add_guests",
    "create_event",
    "get_event",
    "get_guest",
    "get_guests",
    "list_events",
    "list_ticket_types",
    "send_invites",
]

_BASE_URL = "https://public-api.luma.com/v1"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-luma-api-key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateEventInput(BaseModel):
    name: str = Field(description="The event name")
    start_at: str = Field(description="Event start time as ISO 8601 datetime")
    timezone: str = Field(description="IANA timezone, e.g. America/New_York")
    api_key: str = Field(description="Luma API key")
    end_at: str | None = Field(default=None, description="Event end time as ISO 8601 datetime")
    description_md: str | None = Field(default=None, description="Markdown description for the event")
    visibility: str | None = Field(default=None, description="Event visibility: public, members-only, or private")
    slug: str | None = Field(default=None, description="Custom event URL slug")
    meeting_url: str | None = Field(default=None, description="Online meeting URL for a virtual event")
    cover_url: str | None = Field(default=None, description="Cover image URL")
    max_capacity: int | None = Field(default=None, description="Maximum registrations before sold out")
    can_register_for_multiple_tickets: bool | None = Field(default=None, description="Whether guests can register for multiple tickets")
    show_guest_list: bool | None = Field(default=None, description="Whether guests can see who else is attending")
    reminders_disabled: bool | None = Field(default=None, description="Whether to disable default reminders")
    name_requirement: str | None = Field(default=None, description="Name collection: full-name or first-last")
    phone_number_requirement: str | None = Field(default=None, description="Phone number: optional or required")
    tint_color: str | None = Field(default=None, description="Hex color for event theme")
    coordinate_json: str | None = Field(default=None, description="JSON object with latitude and longitude")
    geo_address_json: str | None = Field(default=None, description="JSON object with address details")
    registration_questions_json: str | None = Field(default=None, description="JSON array of registration questions")
    feedback_email_json: str | None = Field(default=None, description="JSON object for post-event feedback email")


class GetEventInput(BaseModel):
    event_id: str = Field(description="Luma event ID (usually starts with evt-)")
    api_key: str = Field(description="Luma API key")


class ListEventsInput(BaseModel):
    api_key: str = Field(description="Luma API key")
    after: str | None = Field(default=None, description="Return events starting after this ISO 8601 datetime")
    before: str | None = Field(default=None, description="Return events starting before this ISO 8601 datetime")
    pagination_cursor: str | None = Field(default=None, description="next_cursor from a previous response")
    pagination_limit: int = Field(default=50, description="Number of items per page")
    status: str | None = Field(default=None, description="Calendar submission status: approved or pending")
    sort_column: str | None = Field(default=None, description="Column to sort by (start_at)")
    sort_direction: str | None = Field(default=None, description="Sort order: asc, desc, asc nulls last, desc nulls last")


class GetGuestInput(BaseModel):
    event_id: str = Field(description="Luma event ID (usually starts with evt-)")
    guest_id: str = Field(description="Guest ID, ticket key, guest key, or email")
    api_key: str = Field(description="Luma API key")


class GetGuestsInput(BaseModel):
    event_id: str = Field(description="Luma event ID (usually starts with evt-)")
    api_key: str = Field(description="Luma API key")
    approval_status: str | None = Field(default=None, description="Filter: approved, session, pending_approval, invited, declined, waitlist")
    pagination_cursor: str | None = Field(default=None, description="next_cursor from a previous response")
    pagination_limit: int = Field(default=50, description="Number of items per page")
    sort_column: str | None = Field(default=None, description="Sort by: name, email, created_at, registered_at, checked_in_at")
    sort_direction: str | None = Field(default=None, description="Sort order: asc, desc, asc nulls last, desc nulls last")


class AddGuestsInput(BaseModel):
    event_id: str = Field(description="Luma event ID (usually starts with evt-)")
    guests_json: str = Field(description="JSON array of guests with at least an email field each")
    api_key: str = Field(description="Luma API key")
    ticket_json: str | None = Field(default=None, description="JSON object assigning one ticket type (mutually exclusive with tickets_json)")
    tickets_json: str | None = Field(default=None, description="JSON array assigning multiple tickets (mutually exclusive with ticket_json)")


class ListTicketTypesInput(BaseModel):
    event_id: str = Field(description="Luma event ID (usually starts with evt-)")
    api_key: str = Field(description="Luma API key")
    include_hidden: bool = Field(default=False, description="Whether to include hidden ticket types")


class SendInvitesInput(BaseModel):
    event_id: str = Field(description="Luma event ID (usually starts with evt-)")
    guests_json: str = Field(description="JSON array of guests to invite with at least an email field each")
    api_key: str = Field(description="Luma API key")
    message: str | None = Field(default=None, description="Optional invite message (max 200 characters)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateEventInput)
@serialize_pydantic_return
async def create_event(
    name: str,
    start_at: str,
    timezone: str,
    api_key: str,
    end_at: str | None = None,
    description_md: str | None = None,
    visibility: str | None = None,
    slug: str | None = None,
    meeting_url: str | None = None,
    cover_url: str | None = None,
    max_capacity: int | None = None,
    can_register_for_multiple_tickets: bool | None = None,
    show_guest_list: bool | None = None,
    reminders_disabled: bool | None = None,
    name_requirement: str | None = None,
    phone_number_requirement: str | None = None,
    tint_color: str | None = None,
    coordinate_json: str | None = None,
    geo_address_json: str | None = None,
    registration_questions_json: str | None = None,
    feedback_email_json: str | None = None,
) -> CreateEventOutput:
    """Create an event on the connected Luma calendar."""
    if not api_key or not api_key.strip():
        return CreateEventOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {
        "name": name,
        "start_at": start_at,
        "timezone": timezone,
    }
    if end_at is not None:
        body["end_at"] = end_at
    if description_md is not None:
        body["description_md"] = description_md
    if visibility is not None:
        body["visibility"] = visibility
    if slug is not None:
        body["slug"] = slug
    if meeting_url is not None:
        body["meeting_url"] = meeting_url
    if cover_url is not None:
        body["cover_url"] = cover_url
    if max_capacity is not None:
        body["max_capacity"] = max_capacity
    if can_register_for_multiple_tickets is not None:
        body["can_register_for_multiple_tickets"] = can_register_for_multiple_tickets
    if show_guest_list is not None:
        body["show_guest_list"] = show_guest_list
    if reminders_disabled is not None:
        body["reminders_disabled"] = reminders_disabled
    if name_requirement is not None:
        body["name_requirement"] = name_requirement
    if phone_number_requirement is not None:
        body["phone_number_requirement"] = phone_number_requirement
    if tint_color is not None:
        body["tint_color"] = tint_color
    if coordinate_json is not None:
        try:
            body["coordinate"] = json.loads(coordinate_json)
        except json.JSONDecodeError:
            return CreateEventOutput(success=False, error="coordinate_json is not valid JSON.")
    if geo_address_json is not None:
        try:
            body["geo_address_json"] = json.loads(geo_address_json)
        except json.JSONDecodeError:
            return CreateEventOutput(success=False, error="geo_address_json is not valid JSON.")
    if registration_questions_json is not None:
        try:
            body["registration_questions"] = json.loads(registration_questions_json)
        except json.JSONDecodeError:
            return CreateEventOutput(success=False, error="registration_questions_json is not valid JSON.")
    if feedback_email_json is not None:
        try:
            body["feedback_email"] = json.loads(feedback_email_json)
        except json.JSONDecodeError:
            return CreateEventOutput(success=False, error="feedback_email_json is not valid JSON.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/event/create",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateEventOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEventOutput(success=False, error=f"Call failed: {exc}")
    return CreateEventOutput(success=True, event=data.get("event") or data)


@tool(args_schema=GetEventInput)
@serialize_pydantic_return
async def get_event(
    event_id: str,
    api_key: str,
) -> GetEventOutput:
    """Get admin details for a Luma event by event ID."""
    if not api_key or not api_key.strip():
        return GetEventOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/event/get",
                headers=_headers(api_key),
                params={"id": event_id},
            )
        if response.status_code != 200:
            return GetEventOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEventOutput(success=False, error=f"Call failed: {exc}")
    return GetEventOutput(success=True, event=data.get("event") or data)


@tool(args_schema=ListEventsInput)
@serialize_pydantic_return
async def list_events(
    api_key: str,
    after: str | None = None,
    before: str | None = None,
    pagination_cursor: str | None = None,
    pagination_limit: int = 50,
    status: str | None = None,
    sort_column: str | None = None,
    sort_direction: str | None = None,
) -> ListEventsOutput:
    """List events managed by the connected Luma calendar."""
    if not api_key or not api_key.strip():
        return ListEventsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"pagination_limit": pagination_limit}
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before
    if pagination_cursor is not None:
        params["pagination_cursor"] = pagination_cursor
    if status is not None:
        params["status"] = status
    if sort_column is not None:
        params["sort_column"] = sort_column
    if sort_direction is not None:
        params["sort_direction"] = sort_direction
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/calendar/list-events",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListEventsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEventsOutput(success=False, error=f"Call failed: {exc}")
    entries = data.get("entries", [])
    events = [e.get("event", e) for e in entries]
    return ListEventsOutput(
        success=True,
        events=events,
        has_more=data.get("has_more"),
        next_cursor=data.get("next_cursor"),
    )


@tool(args_schema=GetGuestInput)
@serialize_pydantic_return
async def get_guest(
    event_id: str,
    guest_id: str,
    api_key: str,
) -> GetGuestOutput:
    """Get detailed information for a Luma event guest by ID or email."""
    if not api_key or not api_key.strip():
        return GetGuestOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/event/get-guest",
                headers=_headers(api_key),
                params={"event_id": event_id, "id": guest_id},
            )
        if response.status_code != 200:
            return GetGuestOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetGuestOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetGuestOutput(success=False, error=f"Call failed: {exc}")
    return GetGuestOutput(success=True, guest=data.get("guest") or data)


@tool(args_schema=GetGuestsInput)
@serialize_pydantic_return
async def get_guests(
    event_id: str,
    api_key: str,
    approval_status: str | None = None,
    pagination_cursor: str | None = None,
    pagination_limit: int = 50,
    sort_column: str | None = None,
    sort_direction: str | None = None,
) -> GetGuestsOutput:
    """List guests registered for, invited to, or waitlisted for a Luma event."""
    if not api_key or not api_key.strip():
        return GetGuestsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"event_id": event_id, "pagination_limit": pagination_limit}
    if approval_status is not None:
        params["approval_status"] = approval_status
    if pagination_cursor is not None:
        params["pagination_cursor"] = pagination_cursor
    if sort_column is not None:
        params["sort_column"] = sort_column
    if sort_direction is not None:
        params["sort_direction"] = sort_direction
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/event/get-guests",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetGuestsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetGuestsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetGuestsOutput(success=False, error=f"Call failed: {exc}")
    entries = data.get("entries", [])
    guests = [e.get("guest", e) for e in entries]
    return GetGuestsOutput(
        success=True,
        guests=guests,
        has_more=data.get("has_more"),
        next_cursor=data.get("next_cursor"),
    )


@tool(args_schema=AddGuestsInput)
@serialize_pydantic_return
async def add_guests(
    event_id: str,
    guests_json: str,
    api_key: str,
    ticket_json: str | None = None,
    tickets_json: str | None = None,
) -> AddGuestsOutput:
    """Add guests to a Luma event with status Going."""
    if not api_key or not api_key.strip():
        return AddGuestsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    if ticket_json and tickets_json:
        return AddGuestsOutput(success=False, error="ticket_json and tickets_json are mutually exclusive.")
    try:
        guests_list = json.loads(guests_json)
    except json.JSONDecodeError:
        return AddGuestsOutput(success=False, error="guests_json is not valid JSON.")
    body: dict[str, Any] = {"event_id": event_id, "guests": guests_list}
    if ticket_json is not None:
        try:
            body["ticket"] = json.loads(ticket_json)
        except json.JSONDecodeError:
            return AddGuestsOutput(success=False, error="ticket_json is not valid JSON.")
    if tickets_json is not None:
        try:
            body["tickets"] = json.loads(tickets_json)
        except json.JSONDecodeError:
            return AddGuestsOutput(success=False, error="tickets_json is not valid JSON.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/event/add-guests",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return AddGuestsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return AddGuestsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddGuestsOutput(success=False, error=f"Call failed: {exc}")
    return AddGuestsOutput(success=True, guests=data.get("guests", []))


@tool(args_schema=ListTicketTypesInput)
@serialize_pydantic_return
async def list_ticket_types(
    event_id: str,
    api_key: str,
    include_hidden: bool = False,
) -> ListTicketTypesOutput:
    """List ticket types for a Luma event."""
    if not api_key or not api_key.strip():
        return ListTicketTypesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"event_id": event_id}
    if include_hidden:
        params["include_hidden"] = "true"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/event/ticket-types/list",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListTicketTypesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListTicketTypesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTicketTypesOutput(success=False, error=f"Call failed: {exc}")
    ticket_types = data.get("ticket_types", data.get("entries", []))
    return ListTicketTypesOutput(success=True, ticket_types=ticket_types)


@tool(args_schema=SendInvitesInput)
@serialize_pydantic_return
async def send_invites(
    event_id: str,
    guests_json: str,
    api_key: str,
    message: str | None = None,
) -> SendInvitesOutput:
    """Send email invitations for a Luma event."""
    if not api_key or not api_key.strip():
        return SendInvitesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        guests_list = json.loads(guests_json)
    except json.JSONDecodeError:
        return SendInvitesOutput(success=False, error="guests_json is not valid JSON.")
    body: dict[str, Any] = {"event_id": event_id, "guests": guests_list}
    if message is not None:
        body["message"] = message
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/event/send-invites",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return SendInvitesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return SendInvitesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendInvitesOutput(success=False, error=f"Call failed: {exc}")
    return SendInvitesOutput(success=True)
