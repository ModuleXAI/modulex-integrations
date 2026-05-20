"""Postman LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.postman.outputs import (
    CreateEnvironmentOutput,
    ListWorkspaceIdOptionsOutput,
    RunMonitorOutput,
    UpdateVariableOutput,
    WorkspaceSummary,
)

__all__ = [
    "create_environment",
    "list_workspace_id_options",
    "run_monitor",
    "update_variable",
]

_BASE_URL = "https://api.getpostman.com"
_TIMEOUT = 30.0


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateEnvironmentInput(BaseModel):
    environment_name: str = Field(description="The name for the new environment")
    api_key: str = Field(description="Postman API key")
    workspace_id: str | None = Field(default=None, description="The ID of the workspace to create the environment in")
    variables: list[dict[str, Any]] | None = Field(default=None, description="List of variable objects with keys: key, value, enabled, type")


class ListWorkspaceIdOptionsInput(BaseModel):
    api_key: str = Field(description="Postman API key")


class RunMonitorInput(BaseModel):
    monitor_id: str = Field(description="The ID of the monitor to run")
    api_key: str = Field(description="Postman API key")


class UpdateVariableInput(BaseModel):
    environment_id: str = Field(description="The ID of the environment containing the variable")
    variable: str = Field(description="The variable key (name) to update")
    variable_value: str = Field(description="The new value for the variable")
    api_key: str = Field(description="Postman API key")
    workspace_id: str | None = Field(default=None, description="The ID of the workspace containing the environment")
    variable_enabled: bool | None = Field(default=None, description="Whether the variable is enabled or not")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateEnvironmentInput)
@serialize_pydantic_return
async def create_environment(
    environment_name: str,
    api_key: str,
    workspace_id: str | None = None,
    variables: list[dict[str, Any]] | None = None,
) -> CreateEnvironmentOutput:
    """Create a new environment in Postman with optional variables."""
    if not api_key or not api_key.strip():
        return CreateEnvironmentOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    values: list[dict[str, Any]] = []
    if variables:
        for var in variables:
            values.append({
                "key": var.get("key", ""),
                "value": var.get("value", ""),
                "enabled": var.get("enabled", True),
                "type": var.get("type", "default"),
            })
    payload: dict[str, Any] = {
        "environment": {
            "name": environment_name,
            "values": values,
        },
    }
    params: dict[str, str] = {}
    if workspace_id:
        params["workspace"] = workspace_id
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/environments",
                headers=_headers(api_key),
                json=payload,
                params=params,
            )
        if response.status_code not in (200, 201):
            return CreateEnvironmentOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateEnvironmentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEnvironmentOutput(success=False, error=f"Call failed: {exc}")
    env = data.get("environment", {})
    return CreateEnvironmentOutput(
        success=True,
        environment_id=env.get("id"),
        environment_name=env.get("name"),
    )


@tool(args_schema=ListWorkspaceIdOptionsInput)
@serialize_pydantic_return
async def list_workspace_id_options(
    api_key: str,
) -> ListWorkspaceIdOptionsOutput:
    """List available workspaces with their IDs and names."""
    if not api_key or not api_key.strip():
        return ListWorkspaceIdOptionsOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/workspaces",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return ListWorkspaceIdOptionsOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListWorkspaceIdOptionsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWorkspaceIdOptionsOutput(success=False, error=f"Call failed: {exc}")
    raw_workspaces = data.get("workspaces", [])
    workspaces = [
        WorkspaceSummary(
            id=w.get("id"),
            name=w.get("name"),
            type=w.get("type"),
        )
        for w in raw_workspaces
    ]
    return ListWorkspaceIdOptionsOutput(success=True, workspaces=workspaces)


@tool(args_schema=RunMonitorInput)
@serialize_pydantic_return
async def run_monitor(
    monitor_id: str,
    api_key: str,
) -> RunMonitorOutput:
    """Run a specific monitor in Postman."""
    if not api_key or not api_key.strip():
        return RunMonitorOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/monitors/{monitor_id}/run",
                headers=_headers(api_key),
            )
        if response.status_code != 200:
            return RunMonitorOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return RunMonitorOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RunMonitorOutput(success=False, error=f"Call failed: {exc}")
    return RunMonitorOutput(success=True, run=data.get("run"))


@tool(args_schema=UpdateVariableInput)
@serialize_pydantic_return
async def update_variable(
    environment_id: str,
    variable: str,
    variable_value: str,
    api_key: str,
    workspace_id: str | None = None,
    variable_enabled: bool | None = None,
) -> UpdateVariableOutput:
    """Update a specific environment variable in Postman."""
    if not api_key or not api_key.strip():
        return UpdateVariableOutput(
            success=False,
            error="API key is empty. Please configure a valid credential.",
        )
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            get_response = await client.get(
                f"{_BASE_URL}/environments/{environment_id}",
                headers=_headers(api_key),
            )
        if get_response.status_code != 200:
            return UpdateVariableOutput(
                success=False,
                error=f"Failed to fetch environment ({get_response.status_code}): {get_response.text}",
            )
        env_data = get_response.json()
        env = env_data.get("environment", {})
        values: list[dict[str, Any]] = env.get("values", [])
        found = False
        for v in values:
            if v.get("key") == variable:
                v["value"] = variable_value
                if variable_enabled is not None:
                    v["enabled"] = variable_enabled
                found = True
                break
        if not found:
            new_var: dict[str, Any] = {
                "key": variable,
                "value": variable_value,
                "enabled": variable_enabled if variable_enabled is not None else True,
                "type": "default",
            }
            values.append(new_var)
        put_payload: dict[str, Any] = {
            "environment": {
                "name": env.get("name", ""),
                "values": values,
            },
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            put_response = await client.put(
                f"{_BASE_URL}/environments/{environment_id}",
                headers=_headers(api_key),
                json=put_payload,
            )
        if put_response.status_code != 200:
            return UpdateVariableOutput(
                success=False,
                error=f"Failed to update environment ({put_response.status_code}): {put_response.text}",
            )
        result_data = put_response.json()
    except httpx.TimeoutException:
        return UpdateVariableOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateVariableOutput(success=False, error=f"Call failed: {exc}")
    result_env = result_data.get("environment", {})
    return UpdateVariableOutput(
        success=True,
        environment_id=result_env.get("id"),
        environment_name=result_env.get("name"),
    )
