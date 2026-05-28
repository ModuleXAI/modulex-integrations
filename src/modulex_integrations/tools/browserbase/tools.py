"""Browserbase LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.browserbase.outputs import (
    CreateContextOutput,
    CreateSessionOutput,
    ListProjectsOutput,
    ProjectSummary,
)

__all__ = [
    "create_context",
    "create_session",
    "list_projects",
]

_BASE_URL = "https://api.browserbase.com/v1"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "x-bb-api-key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateContextInput(BaseModel):
    project_id: str = Field(description="The ID of the Browserbase project")
    api_key: str = Field(description="Browserbase API key")


class CreateSessionInput(BaseModel):
    project_id: str = Field(description="The ID of the Browserbase project")
    api_key: str = Field(description="Browserbase API key")
    extension_id: str | None = Field(default=None, description="The uploaded Extension ID to load in the session")
    browser_settings: dict[str, Any] | None = Field(default=None, description="Settings for the session (e.g. fingerprint, viewport)")
    timeout: int | None = Field(default=None, description="Duration in seconds after which the session will automatically end. Min: 60, Max: 21600.")
    keep_alive: bool | None = Field(default=None, description="Set to true to keep the session alive even after disconnections")
    proxies: list[dict[str, Any]] | None = Field(default=None, description="Array of proxy configuration objects")
    region: str | None = Field(default=None, description="The region where the session should run. One of: us-west-2, us-east-1, eu-central-1, ap-southeast-1.")
    user_metadata: dict[str, Any] | None = Field(default=None, description="Arbitrary user metadata to attach to the session")


class ListProjectsInput(BaseModel):
    api_key: str = Field(description="Browserbase API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateContextInput)
@serialize_pydantic_return
async def create_context(
    project_id: str,
    api_key: str,
) -> CreateContextOutput:
    """Creates a new context in Browserbase for persistent browser state."""
    if not api_key or not api_key.strip():
        return CreateContextOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/contexts",
                headers=_headers(api_key),
                json={"projectId": project_id},
            )
        if response.status_code not in (200, 201):
            return CreateContextOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateContextOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContextOutput(success=False, error=f"Call failed: {exc}")

    return CreateContextOutput(
        success=True,
        id=data.get("id"),
        project_id=data.get("projectId"),
        created_at=data.get("createdAt"),
    )


@tool(args_schema=CreateSessionInput)
@serialize_pydantic_return
async def create_session(
    project_id: str,
    api_key: str,
    extension_id: str | None = None,
    browser_settings: dict[str, Any] | None = None,
    timeout: int | None = None,
    keep_alive: bool | None = None,
    proxies: list[dict[str, Any]] | None = None,
    region: str | None = None,
    user_metadata: dict[str, Any] | None = None,
) -> CreateSessionOutput:
    """Creates a new browser session with specified settings."""
    if not api_key or not api_key.strip():
        return CreateSessionOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    body: dict[str, Any] = {"projectId": project_id}
    if extension_id is not None:
        body["extensionId"] = extension_id
    if browser_settings is not None:
        body["browserSettings"] = browser_settings
    if timeout is not None:
        body["timeout"] = timeout
    if keep_alive is not None:
        body["keepAlive"] = keep_alive
    if proxies is not None:
        body["proxies"] = proxies
    if region is not None:
        body["region"] = region
    if user_metadata is not None:
        body["userMetadata"] = user_metadata

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/sessions",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateSessionOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSessionOutput(success=False, error=f"Call failed: {exc}")

    return CreateSessionOutput(
        success=True,
        id=data.get("id"),
        project_id=data.get("projectId"),
        status=data.get("status"),
        created_at=data.get("createdAt"),
        region=data.get("region"),
        connect_url=data.get("connectUrl"),
    )


@tool(args_schema=ListProjectsInput)
@serialize_pydantic_return
async def list_projects(
    api_key: str,
) -> ListProjectsOutput:
    """Lists all projects in the Browserbase account."""
    if not api_key or not api_key.strip():
        return ListProjectsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/projects",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ListProjectsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListProjectsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProjectsOutput(success=False, error=f"Call failed: {exc}")

    projects = [
        ProjectSummary(id=p.get("id"), name=p.get("name"))
        for p in (data if isinstance(data, list) else [])
    ]
    return ListProjectsOutput(success=True, projects=projects)
