"""Browser Use LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.browser_use.outputs import (
    CreateBrowserSessionOutput,
    CreateProfileOutput,
    CreateSessionOutput,
    CreateWorkspaceOutput,
    DeleteProfileOutput,
    DeleteSessionOutput,
    DeleteWorkspaceFileOutput,
    DeleteWorkspaceOutput,
    GetAccountBillingOutput,
    GetBrowserSessionOutput,
    GetProfileOutput,
    GetSessionOutput,
    GetWorkspaceOutput,
    GetWorkspaceSizeOutput,
    ListBrowserSessionsOutput,
    ListProfilesOutput,
    ListSessionMessagesOutput,
    ListSessionsOutput,
    ListWorkspaceFilesOutput,
    ListWorkspacesOutput,
    StopSessionOutput,
    UpdateBrowserSessionOutput,
    UpdateProfileOutput,
    UpdateWorkspaceOutput,
    UploadWorkspaceFilesOutput,
)

__all__ = [
    "create_browser_session",
    "create_profile",
    "create_session",
    "create_workspace",
    "delete_profile",
    "delete_session",
    "delete_workspace",
    "delete_workspace_file",
    "get_account_billing",
    "get_browser_session",
    "get_profile",
    "get_session",
    "get_workspace",
    "get_workspace_size",
    "list_browser_sessions",
    "list_profiles",
    "list_session_messages",
    "list_sessions",
    "list_workspace_files",
    "list_workspaces",
    "stop_session",
    "update_browser_session",
    "update_profile",
    "update_workspace",
    "upload_workspace_files",
]

_BASE_URL = "https://api.browser-use.com/api/v3"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-Browser-Use-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    task: str | None = Field(default=None, description="Natural-language instruction for the agent")
    model: str = Field(default="claude-sonnet-4.6", description="Browser Use agent model")
    session_id: str | None = Field(default=None, description="ID of an existing session to dispatch a follow-up task to")
    keep_alive: bool = Field(default=False, description="If true, the session stays idle after the task completes")
    max_cost_usd: str | None = Field(default=None, description="Maximum total session cost in USD")
    profile_id: str | None = Field(default=None, description="ID of a Browser Use profile to use")
    workspace_id: str | None = Field(default=None, description="ID of a Browser Use workspace to attach")
    proxy_country_code: str = Field(default="us", description="Lowercase proxy country code for browser traffic")
    output_schema: dict[str, Any] | None = Field(default=None, description="JSON Schema for structured output")
    enable_scheduled_tasks: bool = Field(default=False, description="If true, the agent can create scheduled tasks")
    sensitive_data: dict[str, Any] | None = Field(default=None, description="Key-value pairs available through secure placeholders")
    enable_recording: bool = Field(default=False, description="If true, records the browser session")
    skills: bool = Field(default=True, description="If true, enables built-in agent skills")
    agentmail: bool = Field(default=True, description="If true, provisions a temporary email inbox")
    cache_script: str = Field(default="auto", description="Controls script caching. Allowed: auto, enabled, disabled")
    use_own_key: bool = Field(default=False, description="If true, uses your configured LLM provider key")
    auto_heal: bool = Field(default=True, description="Validates cached script output and reruns if incorrect")


class GetSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    session_id: str = Field(description="ID of the Browser Use agent session")


class ListSessionsInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    page_number: int = Field(default=1, description="Page number to fetch")
    page_size: int = Field(default=20, description="Number of records per page. Maximum: 100")


class DeleteSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    session_id: str = Field(description="ID of the session to delete")


class StopSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    session_id: str = Field(description="ID of the Browser Use agent session")
    strategy: str = Field(default="session", description="Use task or session. Allowed: task, session")


class ListSessionMessagesInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    session_id: str = Field(description="ID of the Browser Use agent session")
    after: str | None = Field(default=None, description="Return messages after this message ID cursor")
    before: str | None = Field(default=None, description="Return messages before this message ID cursor")
    limit: int = Field(default=10, description="Maximum number of messages to return. Maximum: 100")


class CreateBrowserSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    profile_id: str | None = Field(default=None, description="ID of a Browser Use profile")
    proxy_country_code: str = Field(default="us", description="Lowercase proxy country code")
    timeout: int = Field(default=60, description="Session timeout in minutes. Range: 1 to 240")
    browser_screen_width: int | None = Field(default=None, description="Custom browser screen width in pixels")
    browser_screen_height: int | None = Field(default=None, description="Custom browser screen height in pixels")
    allow_resizing: bool = Field(default=False, description="Whether to allow browser resizing")
    custom_proxy: dict[str, Any] | None = Field(default=None, description="Custom proxy object with host, port, username, password")
    enable_recording: bool = Field(default=False, description="If true, records the browser session")


class GetBrowserSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    browser_session_id: str = Field(description="ID of the Browser Use browser session")


class ListBrowserSessionsInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    page_size: int = Field(default=20, description="Number of records per page. Maximum: 100")
    page_number: int = Field(default=1, description="Page number to fetch")
    filter_by: str | None = Field(default=None, description="Filter by status. Allowed: active, stopped")


class UpdateBrowserSessionInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    browser_session_id: str = Field(description="ID of the Browser Use browser session")
    action: str = Field(default="stop", description="Action to perform. Currently supported: stop")


class CreateProfileInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    name: str | None = Field(default=None, description="Profile name. Maximum: 100 characters")
    user_id: str | None = Field(default=None, description="Internal user identifier. Maximum: 255 characters")


class GetProfileInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    profile_id: str = Field(description="ID of the Browser Use profile")


class ListProfilesInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    page_size: int = Field(default=20, description="Number of records per page. Maximum: 100")
    page_number: int = Field(default=1, description="Page number to fetch")
    query: str | None = Field(default=None, description="Search query for profile name or user ID")


class DeleteProfileInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    profile_id: str = Field(description="ID of the profile to delete")


class UpdateProfileInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    profile_id: str = Field(description="ID of the Browser Use profile")
    name: str | None = Field(default=None, description="Updated profile name. Maximum: 100 characters")
    user_id: str | None = Field(default=None, description="Updated internal user identifier")


class CreateWorkspaceInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    name: str | None = Field(default=None, description="Workspace name. Maximum: 100 characters")


class GetWorkspaceInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the Browser Use workspace")


class ListWorkspacesInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    page_size: int = Field(default=20, description="Number of records per page. Maximum: 100")
    page_number: int = Field(default=1, description="Page number to fetch")


class DeleteWorkspaceInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the workspace to delete")


class UpdateWorkspaceInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the Browser Use workspace")
    name: str = Field(description="Updated workspace name. Maximum: 100 characters")


class GetWorkspaceSizeInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the Browser Use workspace")


class ListWorkspaceFilesInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the Browser Use workspace")
    prefix: str | None = Field(default=None, description="Directory prefix to list")
    limit: int = Field(default=50, description="Maximum number of files to return. Maximum: 100")
    cursor: str | None = Field(default=None, description="Pagination cursor from a previous response")
    include_urls: bool = Field(default=False, description="If true, include presigned download URLs")
    shallow: bool = Field(default=False, description="If true, list only immediate files at the prefix")


class DeleteWorkspaceFileInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the Browser Use workspace")
    path: str = Field(description="Relative workspace file path to delete")


class UploadWorkspaceFilesInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")
    workspace_id: str = Field(description="ID of the Browser Use workspace")
    prefix: str | None = Field(default=None, description="Directory prefix to upload into")
    files_json: str = Field(description="JSON array of file metadata objects with name, contentType, and size fields")


class GetAccountBillingInput(BaseModel):
    api_key: str = Field(description="Browser Use API key")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateSessionInput)
@serialize_pydantic_return
async def create_session(
    api_key: str,
    task: str | None = None,
    model: str = "claude-sonnet-4.6",
    session_id: str | None = None,
    keep_alive: bool = False,
    max_cost_usd: str | None = None,
    profile_id: str | None = None,
    workspace_id: str | None = None,
    proxy_country_code: str = "us",
    output_schema: dict[str, Any] | None = None,
    enable_scheduled_tasks: bool = False,
    sensitive_data: dict[str, Any] | None = None,
    enable_recording: bool = False,
    skills: bool = True,
    agentmail: bool = True,
    cache_script: str = "auto",
    use_own_key: bool = False,
    auto_heal: bool = True,
) -> CreateSessionOutput:
    """Create an agent session, dispatch a task, or dispatch a follow-up task to an existing idle session."""
    if not api_key or not api_key.strip():
        return CreateSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")

    proxy_value: str | None = None if proxy_country_code == "none" else proxy_country_code
    cache_value: bool | None = None
    if cache_script == "enabled":
        cache_value = True
    elif cache_script == "disabled":
        cache_value = False

    body: dict[str, Any] = {
        "model": model,
        "keepAlive": keep_alive,
        "enableScheduledTasks": enable_scheduled_tasks,
        "enableRecording": enable_recording,
        "skills": skills,
        "agentmail": agentmail,
        "useOwnKey": use_own_key,
        "autoHeal": auto_heal,
    }
    if task is not None:
        body["task"] = task
    if session_id is not None:
        body["sessionId"] = session_id
    if max_cost_usd is not None:
        body["maxCostUsd"] = float(max_cost_usd)
    if profile_id is not None:
        body["profileId"] = profile_id
    if workspace_id is not None:
        body["workspaceId"] = workspace_id
    if proxy_value is not None:
        body["proxyCountryCode"] = proxy_value
    if output_schema is not None:
        body["outputSchema"] = output_schema
    if sensitive_data is not None:
        body["sensitiveData"] = sensitive_data
    if cache_value is not None:
        body["cacheScript"] = cache_value

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{_BASE_URL}/sessions", headers=_headers(api_key), json=body)
        if response.status_code not in (200, 201):
            return CreateSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateSessionOutput(success=False, error=f"Call failed: {exc}")

    return CreateSessionOutput(
        success=True,
        id=data.get("id"),
        status=data.get("status"),
        task=data.get("task"),
        live_url=data.get("liveUrl"),
        data=data,
    )


@tool(args_schema=GetSessionInput)
@serialize_pydantic_return
async def get_session(
    api_key: str,
    session_id: str,
) -> GetSessionOutput:
    """Get the current state, output, live URL, screenshot URL, and cost details for an agent session."""
    if not api_key or not api_key.strip():
        return GetSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/sessions/{session_id}", headers=_headers(api_key))
        if response.status_code != 200:
            return GetSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetSessionOutput(success=False, error=f"Call failed: {exc}")

    return GetSessionOutput(
        success=True,
        id=data.get("id"),
        status=data.get("status"),
        task=data.get("task"),
        output=data.get("output"),
        live_url=data.get("liveUrl"),
        screenshot_url=data.get("screenshotUrl"),
        cost=data.get("cost"),
        data=data,
    )


@tool(args_schema=ListSessionsInput)
@serialize_pydantic_return
async def list_sessions(
    api_key: str,
    page_number: int = 1,
    page_size: int = 20,
) -> ListSessionsOutput:
    """List Browser Use agent sessions for the authenticated project."""
    if not api_key or not api_key.strip():
        return ListSessionsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/sessions",
                headers=_headers(api_key),
                params={"page": page_number, "page_size": page_size},
            )
        if response.status_code != 200:
            return ListSessionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListSessionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSessionsOutput(success=False, error=f"Call failed: {exc}")

    return ListSessionsOutput(
        success=True,
        sessions=data.get("sessions", []),
        total=data.get("total"),
    )


@tool(args_schema=DeleteSessionInput)
@serialize_pydantic_return
async def delete_session(
    api_key: str,
    session_id: str,
) -> DeleteSessionOutput:
    """Delete an agent session."""
    if not api_key or not api_key.strip():
        return DeleteSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(f"{_BASE_URL}/sessions/{session_id}", headers=_headers(api_key))
        if response.status_code not in (200, 204):
            return DeleteSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteSessionOutput(success=False, error=f"Call failed: {exc}")

    return DeleteSessionOutput(success=True)


@tool(args_schema=StopSessionInput)
@serialize_pydantic_return
async def stop_session(
    api_key: str,
    session_id: str,
    strategy: str = "session",
) -> StopSessionOutput:
    """Stop the current task or stop the entire Browser Use agent session."""
    if not api_key or not api_key.strip():
        return StopSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/sessions/{session_id}/stop",
                headers=_headers(api_key),
                json={"strategy": strategy},
            )
        if response.status_code != 200:
            return StopSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return StopSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return StopSessionOutput(success=False, error=f"Call failed: {exc}")

    return StopSessionOutput(success=True, data=data)


@tool(args_schema=ListSessionMessagesInput)
@serialize_pydantic_return
async def list_session_messages(
    api_key: str,
    session_id: str,
    after: str | None = None,
    before: str | None = None,
    limit: int = 10,
) -> ListSessionMessagesOutput:
    """List messages from a Browser Use agent session, including reasoning, tool calls, browser actions, screenshots, and results."""
    if not api_key or not api_key.strip():
        return ListSessionMessagesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"limit": limit}
    if after is not None:
        params["after"] = after
    if before is not None:
        params["before"] = before
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/sessions/{session_id}/messages",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListSessionMessagesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListSessionMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListSessionMessagesOutput(success=False, error=f"Call failed: {exc}")

    return ListSessionMessagesOutput(success=True, messages=data.get("messages", []))


@tool(args_schema=CreateBrowserSessionInput)
@serialize_pydantic_return
async def create_browser_session(
    api_key: str,
    profile_id: str | None = None,
    proxy_country_code: str = "us",
    timeout: int = 60,
    browser_screen_width: int | None = None,
    browser_screen_height: int | None = None,
    allow_resizing: bool = False,
    custom_proxy: dict[str, Any] | None = None,
    enable_recording: bool = False,
) -> CreateBrowserSessionOutput:
    """Create a standalone browser session for direct browser control through CDP."""
    if not api_key or not api_key.strip():
        return CreateBrowserSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")

    proxy_value: str | None = None if proxy_country_code == "none" else proxy_country_code
    body: dict[str, Any] = {
        "timeout": timeout,
        "allowResizing": allow_resizing,
        "enableRecording": enable_recording,
    }
    if profile_id is not None:
        body["profileId"] = profile_id
    if proxy_value is not None:
        body["proxyCountryCode"] = proxy_value
    if browser_screen_width is not None:
        body["browserScreenWidth"] = browser_screen_width
    if browser_screen_height is not None:
        body["browserScreenHeight"] = browser_screen_height
    if custom_proxy is not None:
        body["customProxy"] = custom_proxy

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{_BASE_URL}/browsers", headers=_headers(api_key), json=body)
        if response.status_code not in (200, 201):
            return CreateBrowserSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateBrowserSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateBrowserSessionOutput(success=False, error=f"Call failed: {exc}")

    return CreateBrowserSessionOutput(
        success=True,
        id=data.get("id"),
        status=data.get("status"),
        live_url=data.get("liveUrl"),
        cdp_url=data.get("cdpUrl"),
        data=data,
    )


@tool(args_schema=GetBrowserSessionInput)
@serialize_pydantic_return
async def get_browser_session(
    api_key: str,
    browser_session_id: str,
) -> GetBrowserSessionOutput:
    """Get details for a standalone browser session, including live URL, CDP URL, status, timeout, and cost fields."""
    if not api_key or not api_key.strip():
        return GetBrowserSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/browsers/{browser_session_id}", headers=_headers(api_key))
        if response.status_code != 200:
            return GetBrowserSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetBrowserSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetBrowserSessionOutput(success=False, error=f"Call failed: {exc}")

    return GetBrowserSessionOutput(
        success=True,
        id=data.get("id"),
        status=data.get("status"),
        live_url=data.get("liveUrl"),
        cdp_url=data.get("cdpUrl"),
        timeout=data.get("timeout"),
        cost=data.get("cost"),
        data=data,
    )


@tool(args_schema=ListBrowserSessionsInput)
@serialize_pydantic_return
async def list_browser_sessions(
    api_key: str,
    page_size: int = 20,
    page_number: int = 1,
    filter_by: str | None = None,
) -> ListBrowserSessionsOutput:
    """List standalone browser sessions for direct browser control via CDP."""
    if not api_key or not api_key.strip():
        return ListBrowserSessionsOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"page_size": page_size, "page": page_number}
    if filter_by is not None:
        params["status"] = filter_by
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/browsers", headers=_headers(api_key), params=params)
        if response.status_code != 200:
            return ListBrowserSessionsOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListBrowserSessionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListBrowserSessionsOutput(success=False, error=f"Call failed: {exc}")

    return ListBrowserSessionsOutput(
        success=True,
        items=data.get("items", []),
        total_items=data.get("totalItems"),
    )


@tool(args_schema=UpdateBrowserSessionInput)
@serialize_pydantic_return
async def update_browser_session(
    api_key: str,
    browser_session_id: str,
    action: str = "stop",
) -> UpdateBrowserSessionOutput:
    """Update a standalone browser session. Currently supports the stop action."""
    if not api_key or not api_key.strip():
        return UpdateBrowserSessionOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/browsers/{browser_session_id}",
                headers=_headers(api_key),
                json={"action": action},
            )
        if response.status_code != 200:
            return UpdateBrowserSessionOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateBrowserSessionOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateBrowserSessionOutput(success=False, error=f"Call failed: {exc}")

    return UpdateBrowserSessionOutput(success=True, data=data)


@tool(args_schema=CreateProfileInput)
@serialize_pydantic_return
async def create_profile(
    api_key: str,
    name: str | None = None,
    user_id: str | None = None,
) -> CreateProfileOutput:
    """Create a profile to preserve cookies, local storage, and login state across sessions."""
    if not api_key or not api_key.strip():
        return CreateProfileOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if user_id is not None:
        body["userId"] = user_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{_BASE_URL}/profiles", headers=_headers(api_key), json=body)
        if response.status_code not in (200, 201):
            return CreateProfileOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateProfileOutput(success=False, error=f"Call failed: {exc}")

    return CreateProfileOutput(success=True, id=data.get("id"), name=data.get("name"), data=data)


@tool(args_schema=GetProfileInput)
@serialize_pydantic_return
async def get_profile(
    api_key: str,
    profile_id: str,
) -> GetProfileOutput:
    """Get a Browser Use profile by ID."""
    if not api_key or not api_key.strip():
        return GetProfileOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/profiles/{profile_id}", headers=_headers(api_key))
        if response.status_code != 200:
            return GetProfileOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetProfileOutput(success=False, error=f"Call failed: {exc}")

    return GetProfileOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        user_id=data.get("userId"),
        data=data,
    )


@tool(args_schema=ListProfilesInput)
@serialize_pydantic_return
async def list_profiles(
    api_key: str,
    page_size: int = 20,
    page_number: int = 1,
    query: str | None = None,
) -> ListProfilesOutput:
    """List Browser Use profiles, optionally searching by profile name or user ID."""
    if not api_key or not api_key.strip():
        return ListProfilesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"page_size": page_size, "page": page_number}
    if query is not None:
        params["query"] = query
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/profiles", headers=_headers(api_key), params=params)
        if response.status_code != 200:
            return ListProfilesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListProfilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProfilesOutput(success=False, error=f"Call failed: {exc}")

    return ListProfilesOutput(
        success=True,
        items=data.get("items", []),
        total_items=data.get("totalItems"),
    )


@tool(args_schema=DeleteProfileInput)
@serialize_pydantic_return
async def delete_profile(
    api_key: str,
    profile_id: str,
) -> DeleteProfileOutput:
    """Delete a Browser Use profile and its persisted browser state."""
    if not api_key or not api_key.strip():
        return DeleteProfileOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(f"{_BASE_URL}/profiles/{profile_id}", headers=_headers(api_key))
        if response.status_code not in (200, 204):
            return DeleteProfileOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteProfileOutput(success=False, error=f"Call failed: {exc}")

    return DeleteProfileOutput(success=True)


@tool(args_schema=UpdateProfileInput)
@serialize_pydantic_return
async def update_profile(
    api_key: str,
    profile_id: str,
    name: str | None = None,
    user_id: str | None = None,
) -> UpdateProfileOutput:
    """Update a Browser Use profile name or user ID."""
    if not api_key or not api_key.strip():
        return UpdateProfileOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    if user_id is not None:
        body["userId"] = user_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(f"{_BASE_URL}/profiles/{profile_id}", headers=_headers(api_key), json=body)
        if response.status_code != 200:
            return UpdateProfileOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateProfileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateProfileOutput(success=False, error=f"Call failed: {exc}")

    return UpdateProfileOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        user_id=data.get("userId"),
        data=data,
    )


@tool(args_schema=CreateWorkspaceInput)
@serialize_pydantic_return
async def create_workspace(
    api_key: str,
    name: str | None = None,
) -> CreateWorkspaceOutput:
    """Create a workspace for persistent shared file storage across sessions."""
    if not api_key or not api_key.strip():
        return CreateWorkspaceOutput(success=False, error="API key is empty. Please configure a valid credential.")
    body: dict[str, Any] = {}
    if name is not None:
        body["name"] = name
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(f"{_BASE_URL}/workspaces", headers=_headers(api_key), json=body)
        if response.status_code not in (200, 201):
            return CreateWorkspaceOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return CreateWorkspaceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateWorkspaceOutput(success=False, error=f"Call failed: {exc}")

    return CreateWorkspaceOutput(success=True, id=data.get("id"), name=data.get("name"), data=data)


@tool(args_schema=GetWorkspaceInput)
@serialize_pydantic_return
async def get_workspace(
    api_key: str,
    workspace_id: str,
) -> GetWorkspaceOutput:
    """Get a Browser Use workspace by ID."""
    if not api_key or not api_key.strip():
        return GetWorkspaceOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/workspaces/{workspace_id}", headers=_headers(api_key))
        if response.status_code != 200:
            return GetWorkspaceOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetWorkspaceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetWorkspaceOutput(success=False, error=f"Call failed: {exc}")

    return GetWorkspaceOutput(success=True, id=data.get("id"), name=data.get("name"), data=data)


@tool(args_schema=ListWorkspacesInput)
@serialize_pydantic_return
async def list_workspaces(
    api_key: str,
    page_size: int = 20,
    page_number: int = 1,
) -> ListWorkspacesOutput:
    """List Browser Use workspaces for persistent shared file storage across sessions."""
    if not api_key or not api_key.strip():
        return ListWorkspacesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/workspaces",
                headers=_headers(api_key),
                params={"page_size": page_size, "page": page_number},
            )
        if response.status_code != 200:
            return ListWorkspacesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListWorkspacesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorkspacesOutput(success=False, error=f"Call failed: {exc}")

    return ListWorkspacesOutput(
        success=True,
        items=data.get("items", []),
        total_items=data.get("totalItems"),
    )


@tool(args_schema=DeleteWorkspaceInput)
@serialize_pydantic_return
async def delete_workspace(
    api_key: str,
    workspace_id: str,
) -> DeleteWorkspaceOutput:
    """Delete a Browser Use workspace and its stored files. This cannot be undone."""
    if not api_key or not api_key.strip():
        return DeleteWorkspaceOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(f"{_BASE_URL}/workspaces/{workspace_id}", headers=_headers(api_key))
        if response.status_code not in (200, 204):
            return DeleteWorkspaceOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteWorkspaceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteWorkspaceOutput(success=False, error=f"Call failed: {exc}")

    return DeleteWorkspaceOutput(success=True)


@tool(args_schema=UpdateWorkspaceInput)
@serialize_pydantic_return
async def update_workspace(
    api_key: str,
    workspace_id: str,
    name: str = "",
) -> UpdateWorkspaceOutput:
    """Update a Browser Use workspace name."""
    if not api_key or not api_key.strip():
        return UpdateWorkspaceOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/workspaces/{workspace_id}",
                headers=_headers(api_key),
                json={"name": name},
            )
        if response.status_code != 200:
            return UpdateWorkspaceOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UpdateWorkspaceOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateWorkspaceOutput(success=False, error=f"Call failed: {exc}")

    return UpdateWorkspaceOutput(success=True, id=data.get("id"), name=data.get("name"), data=data)


@tool(args_schema=GetWorkspaceSizeInput)
@serialize_pydantic_return
async def get_workspace_size(
    api_key: str,
    workspace_id: str,
) -> GetWorkspaceSizeOutput:
    """Get storage usage for a Browser Use workspace."""
    if not api_key or not api_key.strip():
        return GetWorkspaceSizeOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/workspaces/{workspace_id}/size", headers=_headers(api_key))
        if response.status_code != 200:
            return GetWorkspaceSizeOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetWorkspaceSizeOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetWorkspaceSizeOutput(success=False, error=f"Call failed: {exc}")

    return GetWorkspaceSizeOutput(success=True, size_bytes=data.get("sizeBytes"), data=data)


@tool(args_schema=ListWorkspaceFilesInput)
@serialize_pydantic_return
async def list_workspace_files(
    api_key: str,
    workspace_id: str,
    prefix: str | None = None,
    limit: int = 50,
    cursor: str | None = None,
    include_urls: bool = False,
    shallow: bool = False,
) -> ListWorkspaceFilesOutput:
    """List files and folders in a Browser Use workspace, optionally returning presigned download URLs."""
    if not api_key or not api_key.strip():
        return ListWorkspaceFilesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    params: dict[str, Any] = {"limit": limit, "includeUrls": include_urls, "shallow": shallow}
    if prefix is not None:
        params["prefix"] = prefix
    if cursor is not None:
        params["cursor"] = cursor
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/workspaces/{workspace_id}/files",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListWorkspaceFilesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return ListWorkspaceFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorkspaceFilesOutput(success=False, error=f"Call failed: {exc}")

    return ListWorkspaceFilesOutput(
        success=True,
        files=data.get("files", []),
        cursor=data.get("cursor"),
    )


@tool(args_schema=DeleteWorkspaceFileInput)
@serialize_pydantic_return
async def delete_workspace_file(
    api_key: str,
    workspace_id: str,
    path: str,
) -> DeleteWorkspaceFileOutput:
    """Delete a file from a Browser Use workspace."""
    if not api_key or not api_key.strip():
        return DeleteWorkspaceFileOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/workspaces/{workspace_id}/files",
                headers=_headers(api_key),
                params={"path": path},
            )
        if response.status_code not in (200, 204):
            return DeleteWorkspaceFileOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
    except httpx.TimeoutException:
        return DeleteWorkspaceFileOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteWorkspaceFileOutput(success=False, error=f"Call failed: {exc}")

    return DeleteWorkspaceFileOutput(success=True)


@tool(args_schema=UploadWorkspaceFilesInput)
@serialize_pydantic_return
async def upload_workspace_files(
    api_key: str,
    workspace_id: str,
    files_json: str,
    prefix: str | None = None,
) -> UploadWorkspaceFilesOutput:
    """Create presigned upload URLs for workspace files."""
    if not api_key or not api_key.strip():
        return UploadWorkspaceFilesOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        files_list = json.loads(files_json)
    except (json.JSONDecodeError, TypeError) as exc:
        return UploadWorkspaceFilesOutput(success=False, error=f"Invalid files_json: {exc}")

    body: dict[str, Any] = {"files": files_list}
    if prefix is not None:
        body["prefix"] = prefix
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/workspaces/{workspace_id}/files/upload",
                headers=_headers(api_key),
                json=body,
            )
        if response.status_code not in (200, 201):
            return UploadWorkspaceFilesOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return UploadWorkspaceFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UploadWorkspaceFilesOutput(success=False, error=f"Call failed: {exc}")

    return UploadWorkspaceFilesOutput(success=True, files=data.get("files", []))


@tool(args_schema=GetAccountBillingInput)
@serialize_pydantic_return
async def get_account_billing(
    api_key: str,
) -> GetAccountBillingOutput:
    """Get account billing details for the authenticated project."""
    if not api_key or not api_key.strip():
        return GetAccountBillingOutput(success=False, error="API key is empty. Please configure a valid credential.")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/billing/account", headers=_headers(api_key))
        if response.status_code != 200:
            return GetAccountBillingOutput(success=False, error=f"API error ({response.status_code}): {response.text}")
        data = response.json()
    except httpx.TimeoutException:
        return GetAccountBillingOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAccountBillingOutput(success=False, error=f"Call failed: {exc}")

    return GetAccountBillingOutput(success=True, data=data)
