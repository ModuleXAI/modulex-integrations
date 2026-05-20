"""Sentry LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.sentry.outputs import (
    EventSummary,
    IssueSummary,
    ListIssueEventsOutput,
    ListProjectEventsOutput,
    ListProjectIssuesOutput,
    UpdateIssueOutput,
)

__all__ = [
    "list_issue_events",
    "list_project_events",
    "list_project_issues",
    "update_issue",
]

_BASE_URL = "https://sentry.io/api/0"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Sentry API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "bearer_token":
        token = auth_data.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


async def _paginate(
    client: httpx.AsyncClient,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    max_results: int,
) -> list[dict[str, Any]]:
    """Follow Sentry's cursor-based pagination via Link headers."""
    results: list[dict[str, Any]] = []
    next_url: str | None = url
    while next_url and len(results) < max_results:
        response = await client.get(next_url, headers=headers, params=params)
        response.raise_for_status()
        page = response.json()
        results.extend(page)
        params = {}
        next_url = None
        link_header = response.headers.get("link", "")
        for part in link_header.split(","):
            if 'rel="next"' in part and 'results="true"' in part:
                url_part = part.split(";")[0].strip().strip("<>")
                next_url = url_part
                break
    return results[:max_results]


# --- Input schemas --------------------------------------------------------


class ListIssueEventsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    issue_id: str = Field(description="The ID of the issue whose events to list")
    full: bool | None = Field(default=None, description="If true, include the full event body including the stacktrace")
    max_results: int = Field(default=100, description="Maximum number of results to return")


class ListProjectEventsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    organization_slug: str = Field(description="The slug of the organization")
    project_slug: str = Field(description="The slug of the project")
    full: bool | None = Field(default=None, description="If true, include the full event body including the stacktrace")
    max_results: int = Field(default=100, description="Maximum number of results to return")


class ListProjectIssuesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    organization_slug: str = Field(description="The slug of the organization")
    project_slug: str = Field(description="The slug of the project")
    query: str | None = Field(default=None, description="A Sentry structured search query. If not provided an implied 'is:unresolved' is assumed")
    stats_period: str | None = Field(default=None, description="An optional stat period (e.g. '24h', '14d')")
    short_id_lookup: bool | None = Field(default=None, description="If true, short IDs are also looked up by this function")
    max_results: int = Field(default=100, description="Maximum number of results to return")


class UpdateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    issue_id: str = Field(description="The ID of the issue to update")
    status: str | None = Field(default=None, description="New status for the issue: resolved, resolvedInNextRelease, unresolved, ignored")
    assigned_to: str | None = Field(default=None, description="The actor ID or username to assign to this issue")
    has_seen: bool | None = Field(default=None, description="Changes the flag indicating if the user has seen the event")
    is_bookmarked: bool | None = Field(default=None, description="Changes the bookmark flag")
    is_public: bool | None = Field(default=None, description="Sets the issue to public or private")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=ListIssueEventsInput)
@serialize_pydantic_return
async def list_issue_events(
    auth_type: str,
    auth_data: dict[str, Any],
    issue_id: str,
    full: bool | None = None,
    max_results: int = 100,
) -> ListIssueEventsOutput:
    """Return a list of events bound to an issue."""
    if not auth_data.get("token"):
        return ListIssueEventsOutput(success=False, error="Missing or empty auth token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if full is not None:
        params["full"] = str(full).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            data = await _paginate(
                client,
                f"{_BASE_URL}/issues/{issue_id}/events/",
                headers,
                params,
                max_results,
            )
    except httpx.HTTPStatusError as exc:
        return ListIssueEventsOutput(
            success=False,
            error=f"API error ({exc.response.status_code}): {exc.response.text}",
        )
    except httpx.TimeoutException:
        return ListIssueEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListIssueEventsOutput(success=False, error=f"Call failed: {exc}")

    events = [
        EventSummary(
            event_id=e.get("eventID"),
            title=e.get("title"),
            message=e.get("message"),
            platform=e.get("platform"),
            date_created=e.get("dateCreated"),
            date_received=e.get("dateReceived"),
            tags=[{"key": t.get("key"), "value": t.get("value")} for t in e.get("tags", [])],
        )
        for e in data
    ]
    return ListIssueEventsOutput(success=True, events=events)


@tool(args_schema=ListProjectEventsInput)
@serialize_pydantic_return
async def list_project_events(
    auth_type: str,
    auth_data: dict[str, Any],
    organization_slug: str,
    project_slug: str,
    full: bool | None = None,
    max_results: int = 100,
) -> ListProjectEventsOutput:
    """Return a list of events bound to a project."""
    if not auth_data.get("token"):
        return ListProjectEventsOutput(success=False, error="Missing or empty auth token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if full is not None:
        params["full"] = str(full).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            data = await _paginate(
                client,
                f"{_BASE_URL}/projects/{organization_slug}/{project_slug}/events/",
                headers,
                params,
                max_results,
            )
    except httpx.HTTPStatusError as exc:
        return ListProjectEventsOutput(
            success=False,
            error=f"API error ({exc.response.status_code}): {exc.response.text}",
        )
    except httpx.TimeoutException:
        return ListProjectEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProjectEventsOutput(success=False, error=f"Call failed: {exc}")

    events = [
        EventSummary(
            event_id=e.get("eventID"),
            title=e.get("title"),
            message=e.get("message"),
            platform=e.get("platform"),
            date_created=e.get("dateCreated"),
            date_received=e.get("dateReceived"),
            tags=[{"key": t.get("key"), "value": t.get("value")} for t in e.get("tags", [])],
        )
        for e in data
    ]
    return ListProjectEventsOutput(success=True, events=events)


@tool(args_schema=ListProjectIssuesInput)
@serialize_pydantic_return
async def list_project_issues(
    auth_type: str,
    auth_data: dict[str, Any],
    organization_slug: str,
    project_slug: str,
    query: str | None = None,
    stats_period: str | None = None,
    short_id_lookup: bool | None = None,
    max_results: int = 100,
) -> ListProjectIssuesOutput:
    """Return a list of issues bound to a project."""
    if not auth_data.get("token"):
        return ListProjectIssuesOutput(success=False, error="Missing or empty auth token.")
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if query is not None:
        params["query"] = query
    if stats_period is not None:
        params["statsPeriod"] = stats_period
    if short_id_lookup is not None:
        params["shortIdLookup"] = str(short_id_lookup).lower()
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            data = await _paginate(
                client,
                f"{_BASE_URL}/projects/{organization_slug}/{project_slug}/issues/",
                headers,
                params,
                max_results,
            )
    except httpx.HTTPStatusError as exc:
        return ListProjectIssuesOutput(
            success=False,
            error=f"API error ({exc.response.status_code}): {exc.response.text}",
        )
    except httpx.TimeoutException:
        return ListProjectIssuesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProjectIssuesOutput(success=False, error=f"Call failed: {exc}")

    issues = [
        IssueSummary(
            id=i.get("id"),
            title=i.get("title"),
            short_id=i.get("shortId"),
            status=i.get("status"),
            level=i.get("level"),
            permalink=i.get("permalink"),
            assigned_to=(i.get("assignedTo") or {}).get("name") if i.get("assignedTo") else None,
            has_seen=i.get("hasSeen"),
            is_bookmarked=i.get("isBookmarked"),
            is_public=i.get("isPublic"),
            count=i.get("count"),
            first_seen=i.get("firstSeen"),
            last_seen=i.get("lastSeen"),
        )
        for i in data
    ]
    return ListProjectIssuesOutput(success=True, issues=issues)


@tool(args_schema=UpdateIssueInput)
@serialize_pydantic_return
async def update_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    issue_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    has_seen: bool | None = None,
    is_bookmarked: bool | None = None,
    is_public: bool | None = None,
) -> UpdateIssueOutput:
    """Update an individual issue's attributes."""
    if not auth_data.get("token"):
        return UpdateIssueOutput(success=False, error="Missing or empty auth token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    body: dict[str, Any] = {}
    if status is not None:
        body["status"] = status
    if assigned_to is not None:
        body["assignedTo"] = assigned_to
    if has_seen is not None:
        body["hasSeen"] = has_seen
    if is_bookmarked is not None:
        body["isBookmarked"] = is_bookmarked
    if is_public is not None:
        body["isPublic"] = is_public
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/issues/{issue_id}/",
                headers=headers,
                json=body,
            )
        if response.status_code not in (200, 202):
            return UpdateIssueOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateIssueOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateIssueOutput(success=False, error=f"Call failed: {exc}")

    issue = IssueSummary(
        id=data.get("id"),
        title=data.get("title"),
        short_id=data.get("shortId"),
        status=data.get("status"),
        level=data.get("level"),
        permalink=data.get("permalink"),
        assigned_to=(data.get("assignedTo") or {}).get("name") if data.get("assignedTo") else None,
        has_seen=data.get("hasSeen"),
        is_bookmarked=data.get("isBookmarked"),
        is_public=data.get("isPublic"),
        count=data.get("count"),
        first_seen=data.get("firstSeen"),
        last_seen=data.get("lastSeen"),
    )
    return UpdateIssueOutput(success=True, issue=issue)
