"""Google Workspace LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_workspace.outputs import (
    ListActivitiesByAdminOutput,
    ListActivitiesByEventAndAdminOutput,
    ListActivitiesByEventNameOutput,
    ListAllActivitiesOutput,
)

__all__ = [
    "list_activities_by_admin",
    "list_activities_by_event_and_admin",
    "list_activities_by_event_name",
    "list_all_activities",
]

_BASE_URL = "https://admin.googleapis.com/admin/reports/v1"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Google Admin SDK API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _build_params(
    *,
    event_name: str | None = None,
    end_time: str | None = None,
    start_time: str | None = None,
    max_results: int | None = None,
    filters: str | None = None,
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if event_name is not None:
        params["eventName"] = event_name
    if end_time is not None:
        params["endTime"] = end_time
    if start_time is not None:
        params["startTime"] = start_time
    if max_results is not None:
        params["maxResults"] = max_results
    if filters is not None:
        params["filters"] = filters
    return params


# --- Input schemas --------------------------------------------------------


class ListActivitiesByAdminInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    application_name: str = Field(description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep")
    user_key: str = Field(description="Profile ID or email of the administrator to filter activities for")
    event_name: str | None = Field(default=None, description="Name of the event to filter by")
    end_time: str | None = Field(default=None, description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    start_time: str | None = Field(default=None, description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    max_results: int | None = Field(default=None, description="Maximum number of activity records to return per page (default 1000)")
    filters: str | None = Field(default=None, description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)")


class ListActivitiesByEventAndAdminInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    application_name: str = Field(description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep")
    event_name: str = Field(description="Name of the event to filter by")
    user_key: str = Field(description="Profile ID or email of the administrator to filter activities for")
    end_time: str | None = Field(default=None, description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    start_time: str | None = Field(default=None, description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    max_results: int | None = Field(default=None, description="Maximum number of activity records to return per page (default 1000)")
    filters: str | None = Field(default=None, description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)")


class ListActivitiesByEventNameInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    application_name: str = Field(description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep")
    event_name: str = Field(description="Name of the event to filter by")
    end_time: str | None = Field(default=None, description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    start_time: str | None = Field(default=None, description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    max_results: int | None = Field(default=None, description="Maximum number of activity records to return per page (default 1000)")
    filters: str | None = Field(default=None, description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)")


class ListAllActivitiesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    application_name: str = Field(description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep")
    end_time: str | None = Field(default=None, description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    start_time: str | None = Field(default=None, description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)")
    max_results: int | None = Field(default=None, description="Maximum number of activity records to return per page (default 1000)")
    filters: str | None = Field(default=None, description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListActivitiesByAdminInput)
@serialize_pydantic_return
async def list_activities_by_admin(
    auth_type: str,
    auth_data: dict[str, Any],
    application_name: str,
    user_key: str,
    event_name: str | None = None,
    end_time: str | None = None,
    start_time: str | None = None,
    max_results: int | None = None,
    filters: str | None = None,
) -> ListActivitiesByAdminOutput:
    """Retrieve admin console activities for a specific administrator."""
    headers = _get_auth_headers(auth_type, auth_data)
    params = _build_params(
        event_name=event_name,
        end_time=end_time,
        start_time=start_time,
        max_results=max_results,
        filters=filters,
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/activity/users/{user_key}/applications/{application_name}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListActivitiesByAdminOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListActivitiesByAdminOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListActivitiesByAdminOutput(success=False, error=f"Call failed: {exc}")
    return ListActivitiesByAdminOutput(
        success=True,
        activities=data.get("items", []),
    )


@tool(args_schema=ListActivitiesByEventAndAdminInput)
@serialize_pydantic_return
async def list_activities_by_event_and_admin(
    auth_type: str,
    auth_data: dict[str, Any],
    application_name: str,
    event_name: str,
    user_key: str,
    end_time: str | None = None,
    start_time: str | None = None,
    max_results: int | None = None,
    filters: str | None = None,
) -> ListActivitiesByEventAndAdminOutput:
    """Retrieve activities filtered by both a specific event name and administrator."""
    headers = _get_auth_headers(auth_type, auth_data)
    params = _build_params(
        event_name=event_name,
        end_time=end_time,
        start_time=start_time,
        max_results=max_results,
        filters=filters,
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/activity/users/{user_key}/applications/{application_name}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListActivitiesByEventAndAdminOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListActivitiesByEventAndAdminOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListActivitiesByEventAndAdminOutput(success=False, error=f"Call failed: {exc}")
    return ListActivitiesByEventAndAdminOutput(
        success=True,
        activities=data.get("items", []),
    )


@tool(args_schema=ListActivitiesByEventNameInput)
@serialize_pydantic_return
async def list_activities_by_event_name(
    auth_type: str,
    auth_data: dict[str, Any],
    application_name: str,
    event_name: str,
    end_time: str | None = None,
    start_time: str | None = None,
    max_results: int | None = None,
    filters: str | None = None,
) -> ListActivitiesByEventNameOutput:
    """Retrieve activities for all users filtered by a specific event name."""
    headers = _get_auth_headers(auth_type, auth_data)
    params = _build_params(
        event_name=event_name,
        end_time=end_time,
        start_time=start_time,
        max_results=max_results,
        filters=filters,
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/activity/users/all/applications/{application_name}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListActivitiesByEventNameOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListActivitiesByEventNameOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListActivitiesByEventNameOutput(success=False, error=f"Call failed: {exc}")
    return ListActivitiesByEventNameOutput(
        success=True,
        activities=data.get("items", []),
    )


@tool(args_schema=ListAllActivitiesInput)
@serialize_pydantic_return
async def list_all_activities(
    auth_type: str,
    auth_data: dict[str, Any],
    application_name: str,
    end_time: str | None = None,
    start_time: str | None = None,
    max_results: int | None = None,
    filters: str | None = None,
) -> ListAllActivitiesOutput:
    """Retrieve all administrative activities for the account."""
    headers = _get_auth_headers(auth_type, auth_data)
    params = _build_params(
        end_time=end_time,
        start_time=start_time,
        max_results=max_results,
        filters=filters,
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/activity/users/all/applications/{application_name}",
                headers=headers,
                params=params,
            )
        if response.status_code != 200:
            return ListAllActivitiesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAllActivitiesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAllActivitiesOutput(success=False, error=f"Call failed: {exc}")
    return ListAllActivitiesOutput(
        success=True,
        activities=data.get("items", []),
    )
