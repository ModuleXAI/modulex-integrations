"""Calendly LangChain ``@tool`` functions.

Token-based runtime convention: every tool's signature starts with
``auth_type: str, auth_data: dict[str, Any]`` and the modulex runtime
injects both. ``_get_auth_headers`` then picks ``access_token`` (for
``oauth2``) or ``token`` (for ``bearer_token``) out of ``auth_data``
to build the ``Authorization: Bearer …`` header.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.calendly.outputs import (
    CreateInviteeNoShowOutput,
    CreateSchedulingLinkOutput,
    GetCurrentUserOutput,
    GetEventOutput,
    ListEventInviteesOutput,
    ListEventsOutput,
    ListEventTypesOutput,
    ListGroupsOutput,
    ListOrganizationMembersOutput,
    ListUserAvailabilitySchedulesOutput,
    ListWebhookSubscriptionsOutput,
)

__all__ = [
    "create_invitee_no_show",
    "create_scheduling_link",
    "get_current_user",
    "get_event",
    "list_event_invitees",
    "list_event_types",
    "list_events",
    "list_groups",
    "list_organization_members",
    "list_user_availability_schedules",
    "list_webhook_subscriptions",
]

_BASE_URL = "https://api.calendly.com"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if auth_type == "oauth2":
        token = auth_data.get("access_token")
    elif auth_type == "bearer_token":
        token = auth_data.get("token")
    else:
        token = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _api_error(action: str, response: httpx.Response) -> str:
    return f"API error in {action}: {response.status_code} - {response.text}"


def _ensure_uri(value: str, prefix_path: str) -> str:
    """Promote a bare UUID into a full Calendly URI if needed."""
    if value.startswith("https://"):
        return value
    return f"{_BASE_URL}/{prefix_path}/{value}"


def _pagination(payload: dict[str, Any]) -> dict[str, Any]:
    page = payload.get("pagination") or {}
    return {
        "count": page.get("count", 0),
        "next_page_token": page.get("next_page_token"),
        "next_page": page.get("next_page"),
    }


async def _get_resource_uri(
    headers: dict[str, str], path: str = "users/me"
) -> str | None:
    """Helper: resolve current user URI / current organization URI."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/{path}", headers=headers)
        if response.status_code != 200:
            return None
        return (response.json() or {}).get("resource") or None
    except Exception:
        return None


# --- Input schemas ---------------------------------------------------------


class _AuthFields(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2 or bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")


class GetCurrentUserInput(_AuthFields):
    pass


class ListEventsInput(_AuthFields):
    user: str | None = Field(default=None, description="User URI filter")
    organization: str | None = Field(default=None, description="Organization URI filter")
    invitee_email: str | None = Field(default=None, description="Filter by invitee email")
    status: str | None = Field(default=None, description="'active' or 'canceled'")
    min_start_time: str | None = Field(default=None, description="ISO 8601 lower bound")
    max_start_time: str | None = Field(default=None, description="ISO 8601 upper bound")
    count: int = Field(default=20, description="Max results (capped at 100)")
    page_token: str | None = Field(default=None, description="Pagination token")
    sort: str | None = Field(default=None, description="Sort order")


class GetEventInput(_AuthFields):
    event_uuid: str = Field(description="UUID of the event to retrieve")


class ListEventInviteesInput(_AuthFields):
    event_uuid: str = Field(description="UUID of the event")
    email: str | None = Field(default=None, description="Filter by invitee email")
    status: str | None = Field(default=None, description="'active' or 'canceled'")
    count: int = Field(default=20, description="Max results (capped at 100)")
    page_token: str | None = Field(default=None, description="Pagination token")
    sort: str | None = Field(default=None, description="Sort order")


class ListEventTypesInput(_AuthFields):
    user: str | None = Field(default=None, description="User URI filter")
    organization: str | None = Field(default=None, description="Organization URI filter")
    active: bool | None = Field(default=None, description="Filter by active status")
    count: int = Field(default=20, description="Max results (capped at 100)")
    page_token: str | None = Field(default=None, description="Pagination token")
    sort: str | None = Field(default=None, description="Sort order")


class CreateSchedulingLinkInput(_AuthFields):
    owner: str = Field(description="URI or UUID of the event type")
    max_event_count: int = Field(default=1, description="Max events for the link")


class CreateInviteeNoShowInput(_AuthFields):
    invitee_uri: str = Field(description="URI of the invitee to mark as no-show")


class ListUserAvailabilitySchedulesInput(_AuthFields):
    user: str = Field(description="URI or UUID of the user")


class ListOrganizationMembersInput(_AuthFields):
    organization: str | None = Field(default=None, description="Organization URI")
    user: str | None = Field(default=None, description="Filter by user URI")
    count: int = Field(default=20, description="Max results (capped at 100)")
    page_token: str | None = Field(default=None, description="Pagination token")


class ListGroupsInput(_AuthFields):
    organization: str = Field(description="Organization URI")
    count: int = Field(default=20, description="Max results (capped at 100)")
    page_token: str | None = Field(default=None, description="Pagination token")


class ListWebhookSubscriptionsInput(_AuthFields):
    organization: str = Field(description="Organization URI")
    scope: str = Field(description="Scope ('organization' or 'user')")
    user: str | None = Field(default=None, description="User URI (when scope='user')")
    count: int = Field(default=20, description="Max results (capped at 100)")
    page_token: str | None = Field(default=None, description="Pagination token")
    sort: str | None = Field(default=None, description="Sort order")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=GetCurrentUserInput)
@serialize_pydantic_return
async def get_current_user(
    auth_type: str, auth_data: dict[str, Any]
) -> GetCurrentUserOutput:
    """Get the currently authenticated Calendly user."""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/users/me", headers=headers)
        if response.status_code != 200:
            return GetCurrentUserOutput(
                success=False, error=_api_error("get_current_user", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return GetCurrentUserOutput(success=False, error=f"get_current_user failed: {exc}")

    return GetCurrentUserOutput(success=True, resource=body.get("resource") or None)


@tool(args_schema=ListEventsInput)
@serialize_pydantic_return
async def list_events(
    auth_type: str,
    auth_data: dict[str, Any],
    user: str | None = None,
    organization: str | None = None,
    invitee_email: str | None = None,
    status: str | None = None,
    min_start_time: str | None = None,
    max_start_time: str | None = None,
    count: int = 20,
    page_token: str | None = None,
    sort: str | None = None,
) -> ListEventsOutput:
    """List scheduled Calendly events. Defaults to the current user if no filter."""
    headers = _get_auth_headers(auth_type, auth_data)

    if not user and not organization:
        me = await _get_resource_uri(headers, "users/me")
        if isinstance(me, dict):
            user = me.get("uri")

    params: dict[str, Any] = {"count": min(count, 100)}
    for key, value in {
        "user": user,
        "organization": organization,
        "invitee_email": invitee_email,
        "status": status,
        "min_start_time": min_start_time,
        "max_start_time": max_start_time,
        "page_token": page_token,
        "sort": sort,
    }.items():
        if value:
            params[key] = value

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/scheduled_events", headers=headers, params=params
            )
        if response.status_code != 200:
            return ListEventsOutput(
                success=False, error=_api_error("list_events", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListEventsOutput(success=False, error=f"list_events failed: {exc}")

    page = _pagination(body)
    return ListEventsOutput(
        success=True,
        events=body.get("collection") or [],
        count=page["count"] or len(body.get("collection") or []),
        next_page_token=page["next_page_token"],
        next_page=page["next_page"],
    )


@tool(args_schema=GetEventInput)
@serialize_pydantic_return
async def get_event(
    auth_type: str, auth_data: dict[str, Any], event_uuid: str
) -> GetEventOutput:
    """Get detailed information about a specific scheduled event."""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/scheduled_events/{event_uuid}", headers=headers
            )
        if response.status_code != 200:
            return GetEventOutput(success=False, error=_api_error("get_event", response))
        body = response.json() or {}
    except Exception as exc:
        return GetEventOutput(success=False, error=f"get_event failed: {exc}")

    return GetEventOutput(success=True, resource=body.get("resource") or None)


@tool(args_schema=ListEventInviteesInput)
@serialize_pydantic_return
async def list_event_invitees(
    auth_type: str,
    auth_data: dict[str, Any],
    event_uuid: str,
    email: str | None = None,
    status: str | None = None,
    count: int = 20,
    page_token: str | None = None,
    sort: str | None = None,
) -> ListEventInviteesOutput:
    """List invitees for a specific scheduled event."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"count": min(count, 100)}
    for key, value in {
        "email": email,
        "status": status,
        "page_token": page_token,
        "sort": sort,
    }.items():
        if value:
            params[key] = value

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/scheduled_events/{event_uuid}/invitees",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListEventInviteesOutput(
                success=False, error=_api_error("list_event_invitees", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListEventInviteesOutput(
            success=False, error=f"list_event_invitees failed: {exc}"
        )

    page = _pagination(body)
    return ListEventInviteesOutput(
        success=True,
        invitees=body.get("collection") or [],
        count=page["count"] or len(body.get("collection") or []),
        next_page_token=page["next_page_token"],
        next_page=page["next_page"],
    )


@tool(args_schema=ListEventTypesInput)
@serialize_pydantic_return
async def list_event_types(
    auth_type: str,
    auth_data: dict[str, Any],
    user: str | None = None,
    organization: str | None = None,
    active: bool | None = None,
    count: int = 20,
    page_token: str | None = None,
    sort: str | None = None,
) -> ListEventTypesOutput:
    """List event types for a user or organization."""
    headers = _get_auth_headers(auth_type, auth_data)

    if not user and not organization:
        me = await _get_resource_uri(headers, "users/me")
        if isinstance(me, dict):
            user = me.get("uri")

    params: dict[str, Any] = {"count": min(count, 100)}
    if user:
        params["user"] = user
    if organization:
        params["organization"] = organization
    if active is not None:
        params["active"] = str(active).lower()
    if page_token:
        params["page_token"] = page_token
    if sort:
        params["sort"] = sort

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/event_types", headers=headers, params=params
            )
        if response.status_code != 200:
            return ListEventTypesOutput(
                success=False, error=_api_error("list_event_types", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListEventTypesOutput(
            success=False, error=f"list_event_types failed: {exc}"
        )

    page = _pagination(body)
    return ListEventTypesOutput(
        success=True,
        event_types=body.get("collection") or [],
        count=page["count"] or len(body.get("collection") or []),
        next_page_token=page["next_page_token"],
        next_page=page["next_page"],
    )


@tool(args_schema=CreateSchedulingLinkInput)
@serialize_pydantic_return
async def create_scheduling_link(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    max_event_count: int = 1,
) -> CreateSchedulingLinkOutput:
    """Create a single-use scheduling link for an event type."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {
        "max_event_count": max_event_count,
        "owner": _ensure_uri(owner, "event_types"),
        "owner_type": "EventType",
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/scheduling_links", headers=headers, json=payload
            )
        if response.status_code not in (200, 201):
            return CreateSchedulingLinkOutput(
                success=False, error=_api_error("create_scheduling_link", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return CreateSchedulingLinkOutput(
            success=False, error=f"create_scheduling_link failed: {exc}"
        )

    resource = body.get("resource") or {}
    return CreateSchedulingLinkOutput(
        success=True,
        booking_url=resource.get("booking_url"),
        owner=resource.get("owner"),
        owner_type=resource.get("owner_type"),
    )


@tool(args_schema=CreateInviteeNoShowInput)
@serialize_pydantic_return
async def create_invitee_no_show(
    auth_type: str, auth_data: dict[str, Any], invitee_uri: str
) -> CreateInviteeNoShowOutput:
    """Mark an invitee as a no-show."""
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/invitee_no_shows",
                headers=headers,
                json={"invitee": invitee_uri},
            )
        if response.status_code not in (200, 201):
            return CreateInviteeNoShowOutput(
                success=False, error=_api_error("create_invitee_no_show", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return CreateInviteeNoShowOutput(
            success=False, error=f"create_invitee_no_show failed: {exc}"
        )

    return CreateInviteeNoShowOutput(success=True, resource=body.get("resource") or None)


@tool(args_schema=ListUserAvailabilitySchedulesInput)
@serialize_pydantic_return
async def list_user_availability_schedules(
    auth_type: str, auth_data: dict[str, Any], user: str
) -> ListUserAvailabilitySchedulesOutput:
    """List availability schedules for a specific user."""
    headers = _get_auth_headers(auth_type, auth_data)
    user_uri = _ensure_uri(user, "users")

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/user_availability_schedules",
                headers=headers,
                params={"user": user_uri},
            )
        if response.status_code != 200:
            return ListUserAvailabilitySchedulesOutput(
                success=False,
                error=_api_error("list_user_availability_schedules", response),
            )
        body = response.json() or {}
    except Exception as exc:
        return ListUserAvailabilitySchedulesOutput(
            success=False, error=f"list_user_availability_schedules failed: {exc}"
        )

    schedules = body.get("collection") or []
    return ListUserAvailabilitySchedulesOutput(
        success=True, schedules=schedules, count=len(schedules)
    )


@tool(args_schema=ListOrganizationMembersInput)
@serialize_pydantic_return
async def list_organization_members(
    auth_type: str,
    auth_data: dict[str, Any],
    organization: str | None = None,
    user: str | None = None,
    count: int = 20,
    page_token: str | None = None,
) -> ListOrganizationMembersOutput:
    """List members of an organization."""
    headers = _get_auth_headers(auth_type, auth_data)

    if not organization:
        me = await _get_resource_uri(headers, "users/me")
        if isinstance(me, dict):
            organization = me.get("current_organization")

    params: dict[str, Any] = {"count": min(count, 100)}
    if organization:
        params["organization"] = organization
    if user:
        params["user"] = user
    if page_token:
        params["page_token"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/organization_memberships",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListOrganizationMembersOutput(
                success=False, error=_api_error("list_organization_members", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListOrganizationMembersOutput(
            success=False, error=f"list_organization_members failed: {exc}"
        )

    page = _pagination(body)
    return ListOrganizationMembersOutput(
        success=True,
        members=body.get("collection") or [],
        count=page["count"] or len(body.get("collection") or []),
        next_page_token=page["next_page_token"],
        next_page=page["next_page"],
    )


@tool(args_schema=ListGroupsInput)
@serialize_pydantic_return
async def list_groups(
    auth_type: str,
    auth_data: dict[str, Any],
    organization: str,
    count: int = 20,
    page_token: str | None = None,
) -> ListGroupsOutput:
    """List groups within an organization."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"organization": organization, "count": min(count, 100)}
    if page_token:
        params["page_token"] = page_token

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/groups", headers=headers, params=params
            )
        if response.status_code != 200:
            return ListGroupsOutput(
                success=False, error=_api_error("list_groups", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListGroupsOutput(success=False, error=f"list_groups failed: {exc}")

    page = _pagination(body)
    return ListGroupsOutput(
        success=True,
        groups=body.get("collection") or [],
        count=page["count"] or len(body.get("collection") or []),
        next_page_token=page["next_page_token"],
        next_page=page["next_page"],
    )


@tool(args_schema=ListWebhookSubscriptionsInput)
@serialize_pydantic_return
async def list_webhook_subscriptions(
    auth_type: str,
    auth_data: dict[str, Any],
    organization: str,
    scope: str,
    user: str | None = None,
    count: int = 20,
    page_token: str | None = None,
    sort: str | None = None,
) -> ListWebhookSubscriptionsOutput:
    """List webhook subscriptions for an organization or user."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "organization": organization,
        "scope": scope,
        "count": min(count, 100),
    }
    if user:
        params["user"] = user
    if page_token:
        params["page_token"] = page_token
    if sort:
        params["sort"] = sort

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/webhook_subscriptions",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListWebhookSubscriptionsOutput(
                success=False, error=_api_error("list_webhook_subscriptions", response)
            )
        body = response.json() or {}
    except Exception as exc:
        return ListWebhookSubscriptionsOutput(
            success=False, error=f"list_webhook_subscriptions failed: {exc}"
        )

    page = _pagination(body)
    return ListWebhookSubscriptionsOutput(
        success=True,
        webhooks=body.get("collection") or [],
        count=page["count"] or len(body.get("collection") or []),
        next_page_token=page["next_page_token"],
        next_page=page["next_page"],
    )
