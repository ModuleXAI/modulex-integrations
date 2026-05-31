"""Livestorm LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.livestorm.outputs import (
    CreateEventOutput,
    GetEventOutput,
    ListAttendeesFromEventOutput,
    ListEventsOutput,
    ListSessionsOutput,
    RegisterSomeoneForSessionOutput,
    UpdateEventOutput,
)

__all__ = [
    "create_event",
    "get_event",
    "list_attendees_from_event",
    "list_events",
    "list_sessions",
    "register_someone_for_session",
    "update_event",
]

_BASE_URL = "https://api.livestorm.co/v1"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Livestorm API based on auth_type/auth_data."""
    headers: dict[str, str] = {
        "Accept": "application/vnd.api+json",
        "Content-Type": "application/vnd.api+json",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas ------------------------------------------------------------


class CreateEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner_id: str = Field(description="The ID of the user who owns the event")
    title: str = Field(description="The title of the event")
    slug: str | None = Field(default=None, description="The slug of the event")
    status: str | None = Field(default=None, description="The status of the event: draft, published")
    description: str | None = Field(default=None, description="The HTML description of the event")
    recording_enabled: bool | None = Field(default=None, description="Whether the event is recorded")
    chat_enabled: bool | None = Field(default=None, description="Whether the chat is enabled")
    everyone_can_speak: bool | None = Field(default=None, description="Whether everyone can speak")
    detailed_registration_page_enabled: bool | None = Field(default=None, description="Whether the detailed registration page is enabled")
    light_registration_page_enabled: bool | None = Field(default=None, description="Whether the light registration page is enabled")
    recording_public: bool | None = Field(default=None, description="Whether the recording is public")
    show_in_company_page: bool | None = Field(default=None, description="Whether the event is shown in the company page")
    polls_enabled: bool | None = Field(default=None, description="Whether the polls are enabled")
    questions_enabled: bool | None = Field(default=None, description="Whether the questions are enabled")


class GetEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(description="The ID of the event")


class ListAttendeesFromEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(description="The ID of the event")
    role_filter: str | None = Field(default=None, description="Filter by role: participant, team_member")


class ListEventsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    title_filter: str | None = Field(default=None, description="Filter events by title")


class ListSessionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class RegisterSomeoneForSessionInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    session_id: str = Field(description="The ID of the session")
    referrer: str | None = Field(default=None, description="The referrer of the person registering")
    utm_source: str | None = Field(default=None, description="The UTM source")
    utm_medium: str | None = Field(default=None, description="The UTM medium")
    utm_campaign: str | None = Field(default=None, description="The UTM campaign")
    utm_term: str | None = Field(default=None, description="The UTM term")
    utm_content: str | None = Field(default=None, description="The UTM content")
    fields: dict[str, Any] | None = Field(default=None, description="Registration fields as key-value pairs where key is the field ID and value is the field value")


class UpdateEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_id: str = Field(description="The ID of the event")
    owner_id: str = Field(description="The ID of the user who owns the event")
    title: str = Field(description="The title of the event")
    slug: str = Field(description="The slug of the event")
    status: str = Field(description="The status of the event: draft, published")
    description: str = Field(description="The HTML description of the event")
    recording_enabled: bool = Field(description="Whether the event is recorded")
    chat_enabled: bool = Field(description="Whether the chat is enabled")
    everyone_can_speak: bool = Field(description="Whether everyone can speak")
    detailed_registration_page_enabled: bool = Field(description="Whether the detailed registration page is enabled")
    light_registration_page_enabled: bool = Field(description="Whether the light registration page is enabled")
    recording_public: bool = Field(description="Whether the recording is public")
    show_in_company_page: bool = Field(description="Whether the event is shown in the company page")
    polls_enabled: bool = Field(description="Whether the polls are enabled")
    questions_enabled: bool = Field(description="Whether the questions are enabled")


# --- @tool functions ----------------------------------------------------------


@tool(args_schema=CreateEventInput)
@serialize_pydantic_return
async def create_event(
    auth_type: str,
    auth_data: dict[str, Any],
    owner_id: str,
    title: str,
    slug: str | None = None,
    status: str | None = None,
    description: str | None = None,
    recording_enabled: bool | None = None,
    chat_enabled: bool | None = None,
    everyone_can_speak: bool | None = None,
    detailed_registration_page_enabled: bool | None = None,
    light_registration_page_enabled: bool | None = None,
    recording_public: bool | None = None,
    show_in_company_page: bool | None = None,
    polls_enabled: bool | None = None,
    questions_enabled: bool | None = None,
) -> CreateEventOutput:
    """Create a new event."""
    if not auth_data.get("access_token"):
        return CreateEventOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    attributes: dict[str, Any] = {
        "owner_id": owner_id,
        "title": title,
    }
    if slug is not None:
        attributes["slug"] = slug
    if status is not None:
        attributes["status"] = status
    if description is not None:
        attributes["description"] = description
    if recording_enabled is not None:
        attributes["recording_enabled"] = recording_enabled
    if chat_enabled is not None:
        attributes["chat_enabled"] = chat_enabled
    if everyone_can_speak is not None:
        attributes["everyone_can_speak"] = everyone_can_speak
    if detailed_registration_page_enabled is not None:
        attributes["detailed_registration_page_enabled"] = detailed_registration_page_enabled
    if light_registration_page_enabled is not None:
        attributes["light_registration_page_enabled"] = light_registration_page_enabled
    if recording_public is not None:
        attributes["recording_public"] = recording_public
    if show_in_company_page is not None:
        attributes["show_in_company_page"] = show_in_company_page
    if polls_enabled is not None:
        attributes["polls_enabled"] = polls_enabled
    if questions_enabled is not None:
        attributes["questions_enabled"] = questions_enabled

    payload = {"data": {"type": "events", "attributes": attributes}}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/events",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateEventOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEventOutput(success=False, error=f"Call failed: {exc}")

    return CreateEventOutput(success=True, data=data.get("data"))


@tool(args_schema=GetEventInput)
@serialize_pydantic_return
async def get_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
) -> GetEventOutput:
    """Retrieve a single event."""
    if not auth_data.get("access_token"):
        return GetEventOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/events/{event_id}",
                headers=headers,
            )
        if response.status_code != 200:
            return GetEventOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEventOutput(success=False, error=f"Call failed: {exc}")

    return GetEventOutput(success=True, data=data.get("data"))


@tool(args_schema=ListAttendeesFromEventInput)
@serialize_pydantic_return
async def list_attendees_from_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    role_filter: str | None = None,
) -> ListAttendeesFromEventOutput:
    """List all the people linked to all the sessions of an event."""
    if not auth_data.get("access_token"):
        return ListAttendeesFromEventOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {}
    if role_filter is not None:
        params["filter[role]"] = role_filter

    all_items: list[dict[str, Any]] = []
    page_number = 1
    max_pages = 50
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while page_number <= max_pages:
                params["page[number]"] = str(page_number)
                response = await client.get(
                    f"{_BASE_URL}/events/{event_id}/people",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    return ListAttendeesFromEventOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                body = response.json()
                items = body.get("data", [])
                if not items:
                    break
                all_items.extend(items)
                meta = body.get("meta", {})
                if page_number >= meta.get("page_count", 1):
                    break
                page_number += 1
    except httpx.TimeoutException:
        return ListAttendeesFromEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAttendeesFromEventOutput(success=False, error=f"Call failed: {exc}")

    return ListAttendeesFromEventOutput(success=True, data=all_items)


@tool(args_schema=ListEventsInput)
@serialize_pydantic_return
async def list_events(
    auth_type: str,
    auth_data: dict[str, Any],
    title_filter: str | None = None,
) -> ListEventsOutput:
    """List the events of your workspace."""
    if not auth_data.get("access_token"):
        return ListEventsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, str] = {}
    if title_filter is not None:
        params["filter[title]"] = title_filter

    all_items: list[dict[str, Any]] = []
    page_number = 1
    max_pages = 50
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while page_number <= max_pages:
                params["page[number]"] = str(page_number)
                response = await client.get(
                    f"{_BASE_URL}/events",
                    headers=headers,
                    params=params,
                )
                if response.status_code != 200:
                    return ListEventsOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                body = response.json()
                items = body.get("data", [])
                if not items:
                    break
                all_items.extend(items)
                meta = body.get("meta", {})
                if page_number >= meta.get("page_count", 1):
                    break
                page_number += 1
    except httpx.TimeoutException:
        return ListEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEventsOutput(success=False, error=f"Call failed: {exc}")

    return ListEventsOutput(success=True, data=all_items)


@tool(args_schema=ListSessionsInput)
@serialize_pydantic_return
async def list_sessions(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListSessionsOutput:
    """List all your event sessions."""
    if not auth_data.get("access_token"):
        return ListSessionsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    all_items: list[dict[str, Any]] = []
    page_number = 1
    max_pages = 50
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            while page_number <= max_pages:
                response = await client.get(
                    f"{_BASE_URL}/sessions",
                    headers=headers,
                    params={"page[number]": str(page_number)},
                )
                if response.status_code != 200:
                    return ListSessionsOutput(
                        success=False,
                        error=f"API error ({response.status_code}): {response.text}",
                    )
                body = response.json()
                items = body.get("data", [])
                if not items:
                    break
                all_items.extend(items)
                meta = body.get("meta", {})
                if page_number >= meta.get("page_count", 1):
                    break
                page_number += 1
    except httpx.TimeoutException:
        return ListSessionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSessionsOutput(success=False, error=f"Call failed: {exc}")

    return ListSessionsOutput(success=True, data=all_items)


@tool(args_schema=RegisterSomeoneForSessionInput)
@serialize_pydantic_return
async def register_someone_for_session(
    auth_type: str,
    auth_data: dict[str, Any],
    session_id: str,
    referrer: str | None = None,
    utm_source: str | None = None,
    utm_medium: str | None = None,
    utm_campaign: str | None = None,
    utm_term: str | None = None,
    utm_content: str | None = None,
    fields: dict[str, Any] | None = None,
) -> RegisterSomeoneForSessionOutput:
    """Register a new participant for a session."""
    if not auth_data.get("access_token"):
        return RegisterSomeoneForSessionOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)

    attributes: dict[str, Any] = {}
    if referrer is not None:
        attributes["referrer"] = referrer
    if utm_source is not None:
        attributes["utm_source"] = utm_source
    if utm_medium is not None:
        attributes["utm_medium"] = utm_medium
    if utm_campaign is not None:
        attributes["utm_campaign"] = utm_campaign
    if utm_term is not None:
        attributes["utm_term"] = utm_term
    if utm_content is not None:
        attributes["utm_content"] = utm_content

    fields_array: list[dict[str, Any]] = []
    if fields:
        for field_id, value in fields.items():
            fields_array.append({"id": field_id, "value": value})
    if fields_array:
        attributes["fields"] = fields_array

    payload: dict[str, Any] = {
        "data": {"type": "people", "attributes": attributes},
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/sessions/{session_id}/people",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return RegisterSomeoneForSessionOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RegisterSomeoneForSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RegisterSomeoneForSessionOutput(success=False, error=f"Call failed: {exc}")

    return RegisterSomeoneForSessionOutput(success=True, data=data.get("data"))


@tool(args_schema=UpdateEventInput)
@serialize_pydantic_return
async def update_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_id: str,
    owner_id: str,
    title: str,
    slug: str,
    status: str,
    description: str,
    recording_enabled: bool,
    chat_enabled: bool,
    everyone_can_speak: bool,
    detailed_registration_page_enabled: bool,
    light_registration_page_enabled: bool,
    recording_public: bool,
    show_in_company_page: bool,
    polls_enabled: bool,
    questions_enabled: bool,
) -> UpdateEventOutput:
    """Update an event with its full list of attributes."""
    if not auth_data.get("access_token"):
        return UpdateEventOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    attributes: dict[str, Any] = {
        "owner_id": owner_id,
        "title": title,
        "slug": slug,
        "status": status,
        "description": description,
        "recording_enabled": recording_enabled,
        "chat_enabled": chat_enabled,
        "everyone_can_speak": everyone_can_speak,
        "detailed_registration_page_enabled": detailed_registration_page_enabled,
        "light_registration_page_enabled": light_registration_page_enabled,
        "recording_public": recording_public,
        "show_in_company_page": show_in_company_page,
        "polls_enabled": polls_enabled,
        "questions_enabled": questions_enabled,
    }

    payload = {"data": {"type": "events", "attributes": attributes}}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/events/{event_id}",
                headers=headers,
                json=payload,
            )
        if response.status_code != 200:
            return UpdateEventOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateEventOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateEventOutput(success=False, error=f"Call failed: {exc}")

    return UpdateEventOutput(success=True, data=data.get("data"))
