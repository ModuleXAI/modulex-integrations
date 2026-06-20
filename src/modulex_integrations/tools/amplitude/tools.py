"""Amplitude LangChain @tool functions."""
from __future__ import annotations

import base64
import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.amplitude.outputs import (
    EventSegmentationOutput,
    GetActiveUsersOutput,
    GetRevenueOutput,
    GroupIdentifyOutput,
    IdentifyUserOutput,
    ListEventsOutput,
    ProjectEvent,
    RealtimeActiveUsersOutput,
    SendEventOutput,
    UserActivityEvent,
    UserActivityOutput,
    UserData,
    UserProfileOutput,
    UserSearchMatch,
    UserSearchOutput,
)

__all__ = [
    "event_segmentation",
    "get_active_users",
    "get_revenue",
    "group_identify",
    "identify_user",
    "list_events",
    "realtime_active_users",
    "send_event",
    "user_activity",
    "user_profile",
    "user_search",
]

_TIMEOUT = 30.0

# Event ingestion (API key in body / form).
_HTTP_V2_URL = "https://api2.amplitude.com/2/httpapi"
_IDENTIFY_URL = "https://api2.amplitude.com/identify"
_GROUP_IDENTIFY_URL = "https://api2.amplitude.com/groupidentify"

# Dashboard REST API (HTTP Basic with api_key:secret_key).
_USER_SEARCH_URL = "https://amplitude.com/api/2/usersearch"
_USER_ACTIVITY_URL = "https://amplitude.com/api/2/useractivity"
_EVENT_SEGMENTATION_URL = "https://amplitude.com/api/2/events/segmentation"
_ACTIVE_USERS_URL = "https://amplitude.com/api/2/users"
_REALTIME_URL = "https://amplitude.com/api/2/realtime"
_LIST_EVENTS_URL = "https://amplitude.com/api/2/events/list"
_REVENUE_URL = "https://amplitude.com/api/2/revenue/ltv"

# User Profile API (Api-Key header with secret key only).
_USER_PROFILE_URL = "https://profile-api.amplitude.com/v1/userprofile"

# Error message constants.
_NO_API_KEY = "Missing Amplitude API key in auth_data."
_NO_SECRET_DASHBOARD = (
    "Missing Amplitude Secret key in auth_data (required for the Dashboard REST API)."
)
_NO_SECRET_PROFILE = (
    "Missing Amplitude Secret key in auth_data (required for the User Profile API)."
)
_TIMED_OUT = "Request timed out."


# --- Credential helpers ----------------------------------------------------


def _api_key(auth_data: dict[str, Any]) -> str:
    """Return the project API key from auth_data (empty string if absent)."""
    return str(auth_data.get("api_key") or "")


def _secret_key(auth_data: dict[str, Any]) -> str:
    """Return the project Secret key from auth_data (empty string if absent)."""
    return str(auth_data.get("secret_key") or "")


def _basic_auth_headers(auth_data: dict[str, Any]) -> dict[str, str]:
    """Build HTTP Basic auth headers (base64(api_key:secret_key)) for the Dashboard API."""
    token = base64.b64encode(
        f"{_api_key(auth_data)}:{_secret_key(auth_data)}".encode()
    ).decode()
    return {"Authorization": f"Basic {token}", "Accept": "application/json"}


# --- Input schemas ---------------------------------------------------------


class SendEventInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_type: str = Field(
        description='Name of the event (e.g., "page_view", "purchase")'
    )
    user_id: str | None = Field(
        default=None, description="User ID (required if no device_id)"
    )
    device_id: str | None = Field(
        default=None, description="Device ID (required if no user_id)"
    )
    event_properties: dict[str, Any] | None = Field(
        default=None, description="Custom event properties"
    )
    user_properties: dict[str, Any] | None = Field(
        default=None,
        description="User properties to set ($set, $setOnce, $add, $append, $unset)",
    )
    time: int | None = Field(
        default=None, description="Event timestamp in milliseconds since epoch"
    )
    session_id: int | None = Field(
        default=None,
        description="Session start time in milliseconds since epoch (-1 for no session)",
    )
    insert_id: str | None = Field(
        default=None, description="Unique ID for deduplication (within a 7-day window)"
    )
    app_version: str | None = Field(
        default=None, description="Application version string"
    )
    platform: str | None = Field(
        default=None, description='Platform (e.g., "Web", "iOS", "Android")'
    )
    country: str | None = Field(default=None, description="Two-letter country code")
    language: str | None = Field(
        default=None, description='Language code (e.g., "en")'
    )
    ip: str | None = Field(
        default=None,
        description='IP address for geo-location (use "$remote" for request IP)',
    )
    price: float | None = Field(
        default=None, description="Price of the item purchased"
    )
    quantity: int | None = Field(
        default=None, description="Quantity of items purchased"
    )
    revenue: float | None = Field(default=None, description="Revenue amount")
    product_id: str | None = Field(default=None, description="Product identifier")
    revenue_type: str | None = Field(
        default=None, description='Revenue type (e.g., "purchase", "refund")'
    )


class IdentifyUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_properties: dict[str, Any] = Field(
        description="User properties to set ($set, $setOnce, $add, $append, $unset)"
    )
    user_id: str | None = Field(
        default=None, description="User ID (required if no device_id)"
    )
    device_id: str | None = Field(
        default=None, description="Device ID (required if no user_id)"
    )


class GroupIdentifyInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_type: str = Field(
        description='Group classification (e.g., "company", "org_id")'
    )
    group_value: str = Field(
        description='Specific group identifier (e.g., "Acme Corp")'
    )
    group_properties: dict[str, Any] = Field(
        description="Group properties as a JSON object ($set, $setOnce, $add, $append, $unset)"
    )


class UserSearchInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user: str = Field(description="User ID, Device ID, or Amplitude ID to search for")


class UserActivityInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    amplitude_id: str = Field(description="Amplitude internal user ID")
    offset: int | None = Field(
        default=None, description="Offset for pagination (default 0)"
    )
    limit: int | None = Field(
        default=None,
        description="Maximum number of events to return (default 1000, max 1000)",
    )
    direction: str | None = Field(
        default=None,
        description='Sort direction: "latest" or "earliest" (default: latest)',
    )


class UserProfileInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    user_id: str | None = Field(
        default=None, description="External user ID (required if no device_id)"
    )
    device_id: str | None = Field(
        default=None, description="Device ID (required if no user_id)"
    )
    get_amp_props: bool = Field(
        default=False, description="Include Amplitude user properties"
    )
    get_cohort_ids: bool = Field(
        default=False, description="Include cohort IDs the user belongs to"
    )
    get_computations: bool = Field(
        default=False, description="Include computed user properties"
    )


class EventSegmentationInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    event_type: str = Field(description="Event type name to analyze")
    start: str = Field(description="Start date in YYYYMMDD format")
    end: str = Field(description="End date in YYYYMMDD format")
    metric: str | None = Field(
        default=None,
        description=(
            "Metric: uniques, totals, pct_dau, average, histogram, sums, "
            "value_avg, or formula"
        ),
    )
    interval: str | None = Field(
        default=None,
        description="Time interval: 1 (daily), 7 (weekly), or 30 (monthly)",
    )
    group_by: str | None = Field(
        default=None,
        description='Property name to group by (prefix custom user properties with "gp:")',
    )
    limit: int | None = Field(
        default=None, description="Maximum number of group-by values (max 1000)"
    )


class GetActiveUsersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start: str = Field(description="Start date in YYYYMMDD format")
    end: str = Field(description="End date in YYYYMMDD format")
    metric: str | None = Field(
        default=None, description='Metric type: "active" or "new" (default: active)'
    )
    interval: str | None = Field(
        default=None,
        description="Time interval: 1 (daily), 7 (weekly), or 30 (monthly)",
    )


class RealtimeActiveUsersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListEventsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class GetRevenueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    start: str = Field(description="Start date in YYYYMMDD format")
    end: str = Field(description="End date in YYYYMMDD format")
    metric: str | None = Field(
        default=None,
        description="Metric: 0 (ARPU), 1 (ARPPU), 2 (Total Revenue), 3 (Paying Users)",
    )
    interval: str | None = Field(
        default=None,
        description="Time interval: 1 (daily), 7 (weekly), or 30 (monthly)",
    )


# --- Event ingestion (API key) --------------------------------------------


@tool(args_schema=SendEventInput)
@serialize_pydantic_return
async def send_event(
    auth_type: str,
    auth_data: dict[str, Any],
    event_type: str,
    user_id: str | None = None,
    device_id: str | None = None,
    event_properties: dict[str, Any] | None = None,
    user_properties: dict[str, Any] | None = None,
    time: int | None = None,
    session_id: int | None = None,
    insert_id: str | None = None,
    app_version: str | None = None,
    platform: str | None = None,
    country: str | None = None,
    language: str | None = None,
    ip: str | None = None,
    price: float | None = None,
    quantity: int | None = None,
    revenue: float | None = None,
    product_id: str | None = None,
    revenue_type: str | None = None,
) -> SendEventOutput:
    """Track an event in Amplitude using the HTTP V2 API."""
    api_key = _api_key(auth_data)
    if not api_key:
        return SendEventOutput(success=False, error=_NO_API_KEY)

    event: dict[str, Any] = {"event_type": event_type}
    if user_id is not None:
        event["user_id"] = user_id
    if device_id is not None:
        event["device_id"] = device_id
    if time is not None:
        event["time"] = time
    if session_id is not None:
        event["session_id"] = session_id
    if insert_id is not None:
        event["insert_id"] = insert_id
    if app_version is not None:
        event["app_version"] = app_version
    if platform is not None:
        event["platform"] = platform
    if country is not None:
        event["country"] = country
    if language is not None:
        event["language"] = language
    if ip is not None:
        event["ip"] = ip
    if price is not None:
        event["price"] = price
    if quantity is not None:
        event["quantity"] = quantity
    if revenue is not None:
        event["revenue"] = revenue
    if product_id is not None:
        event["product_id"] = product_id
    if revenue_type is not None:
        event["revenue_type"] = revenue_type
    if event_properties is not None:
        event["event_properties"] = event_properties
    if user_properties is not None:
        event["user_properties"] = user_properties

    body: dict[str, Any] = {"api_key": api_key, "events": [event]}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _HTTP_V2_URL,
                headers={"Content-Type": "application/json"},
                json=body,
            )
        if response.status_code != 200:
            return SendEventOutput(
                success=False,
                error=f"Amplitude API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendEventOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return SendEventOutput(success=False, error=f"send_event failed: {exc}")

    return SendEventOutput(
        success=True,
        code=data.get("code", 200),
        events_ingested=data.get("events_ingested", 0),
        payload_size_bytes=data.get("payload_size_bytes", 0),
        server_upload_time=data.get("server_upload_time", 0),
    )


@tool(args_schema=IdentifyUserInput)
@serialize_pydantic_return
async def identify_user(
    auth_type: str,
    auth_data: dict[str, Any],
    user_properties: dict[str, Any],
    user_id: str | None = None,
    device_id: str | None = None,
) -> IdentifyUserOutput:
    """Set user properties in Amplitude using the Identify API.

    Supports $set, $setOnce, $add, $append, $unset operations.
    """
    api_key = _api_key(auth_data)
    if not api_key:
        return IdentifyUserOutput(success=False, error=_NO_API_KEY)

    identification: dict[str, Any] = {}
    if user_id is not None:
        identification["user_id"] = user_id
    if device_id is not None:
        identification["device_id"] = device_id
    identification["user_properties"] = user_properties

    form: dict[str, str] = {
        "api_key": api_key,
        "identification": json.dumps([identification]),
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _IDENTIFY_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=form,
            )
        if response.status_code != 200:
            return IdentifyUserOutput(
                success=False,
                error=f"Amplitude Identify API error ({response.status_code}): {response.text}",
            )
        text = response.text
    except httpx.TimeoutException:
        return IdentifyUserOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return IdentifyUserOutput(success=False, error=f"identify_user failed: {exc}")

    return IdentifyUserOutput(success=True, code=200, message=text or None)


@tool(args_schema=GroupIdentifyInput)
@serialize_pydantic_return
async def group_identify(
    auth_type: str,
    auth_data: dict[str, Any],
    group_type: str,
    group_value: str,
    group_properties: dict[str, Any],
) -> GroupIdentifyOutput:
    """Set group-level properties in Amplitude.

    Supports $set, $setOnce, $add, $append, $unset operations.
    """
    api_key = _api_key(auth_data)
    if not api_key:
        return GroupIdentifyOutput(success=False, error=_NO_API_KEY)

    identification: dict[str, Any] = {
        "group_type": group_type,
        "group_value": group_value,
        "group_properties": group_properties,
    }
    form: dict[str, str] = {
        "api_key": api_key,
        "identification": json.dumps([identification]),
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                _GROUP_IDENTIFY_URL,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data=form,
            )
        if response.status_code != 200:
            return GroupIdentifyOutput(
                success=False,
                error=f"Group Identify API error ({response.status_code}): {response.text}",
            )
        text = response.text
    except httpx.TimeoutException:
        return GroupIdentifyOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return GroupIdentifyOutput(success=False, error=f"group_identify failed: {exc}")

    return GroupIdentifyOutput(success=True, code=200, message=text or None)


# --- Dashboard REST API (Basic auth) --------------------------------------


@tool(args_schema=UserSearchInput)
@serialize_pydantic_return
async def user_search(
    auth_type: str,
    auth_data: dict[str, Any],
    user: str,
) -> UserSearchOutput:
    """Search for a user by User ID, Device ID, or Amplitude ID via the Dashboard REST API."""
    if not _api_key(auth_data):
        return UserSearchOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return UserSearchOutput(success=False, error=_NO_SECRET_DASHBOARD)

    params: dict[str, Any] = {"user": user.strip()}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _USER_SEARCH_URL,
                headers=_basic_auth_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return UserSearchOutput(
                success=False,
                error=f"Amplitude User Search API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UserSearchOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return UserSearchOutput(success=False, error=f"user_search failed: {exc}")

    matches = [
        UserSearchMatch(
            amplitude_id=m.get("amplitude_id"),
            user_id=m.get("user_id"),
        )
        for m in (data.get("matches") or [])
    ]
    return UserSearchOutput(success=True, matches=matches, type=data.get("type"))


@tool(args_schema=UserActivityInput)
@serialize_pydantic_return
async def user_activity(
    auth_type: str,
    auth_data: dict[str, Any],
    amplitude_id: str,
    offset: int | None = None,
    limit: int | None = None,
    direction: str | None = None,
) -> UserActivityOutput:
    """Get the event stream for a specific user by their Amplitude ID."""
    if not _api_key(auth_data):
        return UserActivityOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return UserActivityOutput(success=False, error=_NO_SECRET_DASHBOARD)

    params: dict[str, Any] = {"user": amplitude_id.strip()}
    if offset is not None:
        params["offset"] = offset
    if limit is not None:
        params["limit"] = limit
    if direction is not None:
        params["direction"] = direction

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _USER_ACTIVITY_URL,
                headers=_basic_auth_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return UserActivityOutput(
                success=False,
                error=f"User Activity API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UserActivityOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return UserActivityOutput(success=False, error=f"user_activity failed: {exc}")

    events = [
        UserActivityEvent(
            event_type=e.get("event_type"),
            event_time=e.get("event_time"),
            event_properties=e.get("event_properties") or {},
            user_properties=e.get("user_properties") or {},
            session_id=e.get("session_id"),
            platform=e.get("platform"),
            country=e.get("country"),
            city=e.get("city"),
        )
        for e in (data.get("events") or [])
    ]

    ud = data.get("userData")
    user_data = (
        UserData(
            user_id=ud.get("user_id"),
            canonical_amplitude_id=ud.get("canonical_amplitude_id"),
            num_events=ud.get("num_events"),
            num_sessions=ud.get("num_sessions"),
            platform=ud.get("platform"),
            country=ud.get("country"),
        )
        if isinstance(ud, dict)
        else None
    )

    return UserActivityOutput(success=True, events=events, user_data=user_data)


@tool(args_schema=EventSegmentationInput)
@serialize_pydantic_return
async def event_segmentation(
    auth_type: str,
    auth_data: dict[str, Any],
    event_type: str,
    start: str,
    end: str,
    metric: str | None = None,
    interval: str | None = None,
    group_by: str | None = None,
    limit: int | None = None,
) -> EventSegmentationOutput:
    """Query event analytics data with segmentation (counts, uniques, averages, and more)."""
    if not _api_key(auth_data):
        return EventSegmentationOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return EventSegmentationOutput(success=False, error=_NO_SECRET_DASHBOARD)

    params: dict[str, Any] = {
        "e": json.dumps({"event_type": event_type}),
        "start": start,
        "end": end,
    }
    if metric is not None:
        params["m"] = metric
    if interval is not None:
        params["i"] = interval
    if group_by is not None:
        params["g"] = group_by
    if limit is not None:
        params["limit"] = limit

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _EVENT_SEGMENTATION_URL,
                headers=_basic_auth_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return EventSegmentationOutput(
                success=False,
                error=f"Event Segmentation API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return EventSegmentationOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return EventSegmentationOutput(
            success=False, error=f"event_segmentation failed: {exc}"
        )

    result = data.get("data") or {}
    return EventSegmentationOutput(
        success=True,
        series=result.get("series") or [],
        series_labels=result.get("seriesLabels") or [],
        series_collapsed=result.get("seriesCollapsed") or [],
        x_values=result.get("xValues") or [],
    )


@tool(args_schema=GetActiveUsersInput)
@serialize_pydantic_return
async def get_active_users(
    auth_type: str,
    auth_data: dict[str, Any],
    start: str,
    end: str,
    metric: str | None = None,
    interval: str | None = None,
) -> GetActiveUsersOutput:
    """Get active or new user counts over a date range from the Dashboard REST API."""
    if not _api_key(auth_data):
        return GetActiveUsersOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return GetActiveUsersOutput(success=False, error=_NO_SECRET_DASHBOARD)

    params: dict[str, Any] = {"start": start, "end": end}
    if metric is not None:
        params["m"] = metric
    if interval is not None:
        params["i"] = interval

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _ACTIVE_USERS_URL,
                headers=_basic_auth_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return GetActiveUsersOutput(
                success=False,
                error=f"Amplitude Active Users API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetActiveUsersOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return GetActiveUsersOutput(
            success=False, error=f"get_active_users failed: {exc}"
        )

    result = data.get("data") or {}
    return GetActiveUsersOutput(
        success=True,
        series=result.get("series") or [],
        series_meta=result.get("seriesMeta") or [],
        x_values=result.get("xValues") or [],
    )


@tool(args_schema=RealtimeActiveUsersInput)
@serialize_pydantic_return
async def realtime_active_users(
    auth_type: str,
    auth_data: dict[str, Any],
) -> RealtimeActiveUsersOutput:
    """Get real-time active user counts at 5-minute granularity for the last 2 days."""
    if not _api_key(auth_data):
        return RealtimeActiveUsersOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return RealtimeActiveUsersOutput(success=False, error=_NO_SECRET_DASHBOARD)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _REALTIME_URL,
                headers=_basic_auth_headers(auth_data),
            )
        if response.status_code != 200:
            return RealtimeActiveUsersOutput(
                success=False,
                error=f"Amplitude Real-time API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RealtimeActiveUsersOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return RealtimeActiveUsersOutput(
            success=False, error=f"realtime_active_users failed: {exc}"
        )

    result = data.get("data") or {}
    return RealtimeActiveUsersOutput(
        success=True,
        series=result.get("series") or [],
        series_labels=result.get("seriesLabels") or [],
        x_values=result.get("xValues") or [],
    )


@tool(args_schema=ListEventsInput)
@serialize_pydantic_return
async def list_events(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListEventsOutput:
    """List all event types in the project with their weekly totals and unique counts."""
    if not _api_key(auth_data):
        return ListEventsOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return ListEventsOutput(success=False, error=_NO_SECRET_DASHBOARD)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _LIST_EVENTS_URL,
                headers=_basic_auth_headers(auth_data),
            )
        if response.status_code != 200:
            return ListEventsOutput(
                success=False,
                error=f"Amplitude List Events API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListEventsOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return ListEventsOutput(success=False, error=f"list_events failed: {exc}")

    events = [
        ProjectEvent(
            value=e.get("value"),
            display_name=e.get("display"),
            totals=e.get("totals"),
            hidden=e.get("hidden"),
            deleted=e.get("deleted"),
        )
        for e in (data.get("data") or [])
    ]
    return ListEventsOutput(success=True, events=events)


@tool(args_schema=GetRevenueInput)
@serialize_pydantic_return
async def get_revenue(
    auth_type: str,
    auth_data: dict[str, Any],
    start: str,
    end: str,
    metric: str | None = None,
    interval: str | None = None,
) -> GetRevenueOutput:
    """Get revenue LTV data including ARPU, ARPPU, total revenue, and paying user counts."""
    if not _api_key(auth_data):
        return GetRevenueOutput(success=False, error=_NO_API_KEY)
    if not _secret_key(auth_data):
        return GetRevenueOutput(success=False, error=_NO_SECRET_DASHBOARD)

    params: dict[str, Any] = {"start": start, "end": end}
    if metric is not None:
        params["m"] = metric
    if interval is not None:
        params["i"] = interval

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _REVENUE_URL,
                headers=_basic_auth_headers(auth_data),
                params=params,
            )
        if response.status_code != 200:
            return GetRevenueOutput(
                success=False,
                error=f"Amplitude Revenue API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetRevenueOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return GetRevenueOutput(success=False, error=f"get_revenue failed: {exc}")

    result = data.get("data") or {}
    return GetRevenueOutput(
        success=True,
        series=result.get("series") or [],
        series_labels=result.get("seriesLabels") or [],
        x_values=result.get("xValues") or [],
    )


# --- User Profile API (Api-Key header, secret key only) -------------------


@tool(args_schema=UserProfileInput)
@serialize_pydantic_return
async def user_profile(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str | None = None,
    device_id: str | None = None,
    get_amp_props: bool = False,
    get_cohort_ids: bool = False,
    get_computations: bool = False,
) -> UserProfileOutput:
    """Get a user profile including properties, cohort memberships, and computed properties."""
    secret_key = _secret_key(auth_data)
    if not secret_key:
        return UserProfileOutput(success=False, error=_NO_SECRET_PROFILE)

    params: dict[str, Any] = {}
    if user_id is not None:
        params["user_id"] = user_id.strip()
    if device_id is not None:
        params["device_id"] = device_id.strip()
    if get_amp_props:
        params["get_amp_props"] = "true"
    if get_cohort_ids:
        params["get_cohort_ids"] = "true"
    if get_computations:
        params["get_computations"] = "true"

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                _USER_PROFILE_URL,
                headers={"Authorization": f"Api-Key {secret_key}"},
                params=params,
            )
        if response.status_code != 200:
            return UserProfileOutput(
                success=False,
                error=f"Amplitude User Profile API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UserProfileOutput(success=False, error=_TIMED_OUT)
    except Exception as exc:
        return UserProfileOutput(success=False, error=f"user_profile failed: {exc}")

    profile = data.get("userData") or {}
    return UserProfileOutput(
        success=True,
        user_id=profile.get("user_id"),
        device_id=profile.get("device_id"),
        amp_props=profile.get("amp_props"),
        cohort_ids=profile.get("cohort_ids"),
        computations=profile.get("computations"),
    )
