"""Reflect LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.reflect.outputs import (
    AppendDailyNoteOutput,
    CreateLinkOutput,
    GetUserOutput,
    LinkItem,
    ListGraphIdOptionsOutput,
    ListLinksOutput,
)

__all__ = [
    "append_daily_note",
    "create_link",
    "get_user",
    "list_graph_id_options",
    "list_links",
]

_BASE_URL = "https://reflect.app/api"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Reflect API based on auth_type/auth_data."""
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


# --- Input schemas --------------------------------------------------------


class AppendDailyNoteInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    graph_id: str = Field(description="The graph identifier")
    text: str = Field(description="Text to append to the daily note")
    list_name: str | None = Field(default=None, description="Name of the list to append to")
    date: str | None = Field(
        default=None, description="Date of the daily note in ISO 8601 format. Defaults to today."
    )


class CreateLinkInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    graph_id: str = Field(description="The graph identifier")
    url: str = Field(description="The URL of the link to create")
    title: str | None = Field(default=None, description="The link title")
    description: str | None = Field(default=None, description="The link description")


class GetUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListGraphIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class ListLinksInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    graph_id: str = Field(description="The graph identifier")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=AppendDailyNoteInput)
@serialize_pydantic_return
async def append_daily_note(
    auth_type: str,
    auth_data: dict[str, Any],
    graph_id: str,
    text: str,
    list_name: str | None = None,
    date: str | None = None,
) -> AppendDailyNoteOutput:
    """Append to a daily note."""
    if not auth_data.get("access_token"):
        return AppendDailyNoteOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {
        "text": text,
        "transform_type": "list-append",
    }
    if list_name is not None:
        payload["list_name"] = list_name
    if date is not None:
        payload["date"] = date
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{_BASE_URL}/graphs/{graph_id}/daily-notes",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201, 204):
            return AppendDailyNoteOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AppendDailyNoteOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AppendDailyNoteOutput(success=False, error=f"Call failed: {exc}")
    return AppendDailyNoteOutput(success=True)


@tool(args_schema=CreateLinkInput)
@serialize_pydantic_return
async def create_link(
    auth_type: str,
    auth_data: dict[str, Any],
    graph_id: str,
    url: str,
    title: str | None = None,
    description: str | None = None,
) -> CreateLinkOutput:
    """Create a new link."""
    if not auth_data.get("access_token"):
        return CreateLinkOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    headers["Content-Type"] = "application/json"
    payload: dict[str, Any] = {"url": url}
    if title is not None:
        payload["title"] = title
    if description is not None:
        payload["description"] = description
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/graphs/{graph_id}/links",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateLinkOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateLinkOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateLinkOutput(success=False, error=f"Call failed: {exc}")
    return CreateLinkOutput(success=True, id=data.get("id"))


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetUserOutput:
    """Retieves information about the authenticated user."""
    if not auth_data.get("access_token"):
        return GetUserOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/users/me",
                headers=headers,
            )
        if response.status_code != 200:
            return GetUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetUserOutput(success=False, error=f"Call failed: {exc}")
    return GetUserOutput(
        success=True,
        uid=data.get("uid"),
        graph_ids=data.get("graph_ids", []),
    )


@tool(args_schema=ListGraphIdOptionsInput)
@serialize_pydantic_return
async def list_graph_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListGraphIdOptionsOutput:
    """Retrieves available options for the GraphId field."""
    if not auth_data.get("access_token"):
        return ListGraphIdOptionsOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/users/me",
                headers=headers,
            )
        if response.status_code != 200:
            return ListGraphIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListGraphIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListGraphIdOptionsOutput(success=False, error=f"Call failed: {exc}")
    return ListGraphIdOptionsOutput(
        success=True,
        graph_ids=data.get("graph_ids", []),
    )


@tool(args_schema=ListLinksInput)
@serialize_pydantic_return
async def list_links(
    auth_type: str,
    auth_data: dict[str, Any],
    graph_id: str,
) -> ListLinksOutput:
    """Retieve all links for a graph."""
    if not auth_data.get("access_token"):
        return ListLinksOutput(success=False, error="Missing OAuth2 access token.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/graphs/{graph_id}/links",
                headers=headers,
            )
        if response.status_code != 200:
            return ListLinksOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListLinksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListLinksOutput(success=False, error=f"Call failed: {exc}")
    links = [
        LinkItem(
            id=item.get("id"),
            url=item.get("url"),
            title=item.get("title"),
            description=item.get("description"),
            updated_at=item.get("updated_at"),
        )
        for item in (data if isinstance(data, list) else [])
    ]
    return ListLinksOutput(success=True, links=links)
