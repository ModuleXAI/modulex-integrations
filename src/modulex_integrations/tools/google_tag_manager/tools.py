"""Google Tag Manager LangChain @tool functions."""
from __future__ import annotations

import json
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_tag_manager.outputs import (
    AccountItem,
    CreateTagOutput,
    GetTagOutput,
    GetTagsOutput,
    ListAccountIdOptionsOutput,
    TagResource,
    UpdateTagOutput,
    UpdateVariableOutput,
)

__all__ = [
    "create_tag",
    "get_tag",
    "get_tags",
    "list_account_id_options",
    "update_tag",
    "update_variable",
]

_BASE_URL = "https://www.googleapis.com/tagmanager/v2"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_tag(t: dict[str, Any]) -> TagResource:
    return TagResource(
        tag_id=t.get("tagId"),
        name=t.get("name"),
        type=t.get("type"),
        live_only=t.get("liveOnly"),
        notes=t.get("notes"),
        parameter=t.get("parameter") or [],
        fingerprint=t.get("fingerprint"),
        tag_manager_url=t.get("tagManagerUrl"),
        path=t.get("path"),
        account_id=t.get("accountId"),
        container_id=t.get("containerId"),
        workspace_id=t.get("workspaceId"),
    )


def _safe_json_loads(value: str | None) -> Any:
    if value is None:
        return None
    return json.loads(value)


# --- Input schemas --------------------------------------------------------


class CreateTagInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="The Google Tag Manager account ID")
    container_id: str = Field(description="The container ID")
    workspace_id: str = Field(description="The workspace ID")
    name: str = Field(description="The name of the tag")
    type: str = Field(description="The type of the tag (see Tag Dictionary Reference)")
    parameter: str = Field(description="JSON string representing the list of parameters for the tag")
    live_only: bool | None = Field(default=None, description="Whether the tag should only fire in the live environment")
    notes: str | None = Field(default=None, description="Any notes or comments about the tag")
    consent_settings: str | None = Field(default=None, description="JSON string representing consent settings for the tag")
    monitoring_metadata: str | None = Field(default=None, description="JSON string representing monitoring metadata for the tag")


class GetTagInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="The Google Tag Manager account ID")
    container_id: str = Field(description="The container ID")
    workspace_id: str = Field(description="The workspace ID")
    tag_id: str = Field(description="The tag ID")


class GetTagsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="The Google Tag Manager account ID")
    container_id: str = Field(description="The container ID")
    workspace_id: str = Field(description="The workspace ID")


class ListAccountIdOptionsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")


class UpdateTagInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="The Google Tag Manager account ID")
    container_id: str = Field(description="The container ID")
    workspace_id: str = Field(description="The workspace ID")
    tag_id: str = Field(description="The tag ID")
    type: str = Field(description="The type of the tag (see Tag Dictionary Reference)")
    parameter: str = Field(description="JSON string representing the list of parameters for the tag")
    name: str | None = Field(default=None, description="The name of the tag")
    live_only: bool | None = Field(default=None, description="Whether the tag should only fire in the live environment")
    notes: str | None = Field(default=None, description="Any notes or comments about the tag")
    consent_settings: str | None = Field(default=None, description="JSON string representing consent settings for the tag")
    monitoring_metadata: str | None = Field(default=None, description="JSON string representing monitoring metadata for the tag")


class UpdateVariableInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    account_id: str = Field(description="The Google Tag Manager account ID")
    container_id: str = Field(description="The container ID")
    workspace_id: str = Field(description="The workspace ID")
    variable_id: str = Field(description="The variable ID")
    name: str = Field(description="The name of the variable")
    type: str = Field(description="The type of the variable (e.g. 'jsm')")
    parameter: str = Field(description="JSON string representing the list of parameters for the variable")
    format_value: str | None = Field(default=None, description="JSON string representing the formatValue object for the variable")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateTagInput)
@serialize_pydantic_return
async def create_tag(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    container_id: str,
    workspace_id: str,
    name: str,
    type: str,
    parameter: str,
    live_only: bool | None = None,
    notes: str | None = None,
    consent_settings: str | None = None,
    monitoring_metadata: str | None = None,
) -> CreateTagOutput:
    """Create a tag in a Google Tag Manager workspace."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "name": name,
        "type": type,
        "parameter": _safe_json_loads(parameter),
    }
    if live_only is not None:
        body["liveOnly"] = live_only
    if notes is not None:
        body["notes"] = notes
    if consent_settings is not None:
        body["consentSettings"] = _safe_json_loads(consent_settings)
    if monitoring_metadata is not None:
        body["monitoringMetadata"] = _safe_json_loads(monitoring_metadata)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/tags",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return CreateTagOutput(success=True, tag=_parse_tag(data))


@tool(args_schema=GetTagInput)
@serialize_pydantic_return
async def get_tag(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    container_id: str,
    workspace_id: str,
    tag_id: str,
) -> GetTagOutput:
    """Get a specific tag from a Google Tag Manager workspace."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/tags/{tag_id}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetTagOutput(success=True, tag=_parse_tag(data))


@tool(args_schema=GetTagsInput)
@serialize_pydantic_return
async def get_tags(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    container_id: str,
    workspace_id: str,
) -> GetTagsOutput:
    """List all tags in a Google Tag Manager workspace."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/tags",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    tags = [_parse_tag(t) for t in data.get("tag", [])]
    return GetTagsOutput(success=True, tags=tags)


@tool(args_schema=ListAccountIdOptionsInput)
@serialize_pydantic_return
async def list_account_id_options(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListAccountIdOptionsOutput:
    """List available Google Tag Manager accounts."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/accounts",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    accounts = [
        AccountItem(
            account_id=a.get("accountId"),
            name=a.get("name"),
            share_data=a.get("shareData"),
            fingerprint=a.get("fingerprint"),
            path=a.get("path"),
            tag_manager_url=a.get("tagManagerUrl"),
        )
        for a in data.get("account", [])
    ]
    return ListAccountIdOptionsOutput(success=True, accounts=accounts)


@tool(args_schema=UpdateTagInput)
@serialize_pydantic_return
async def update_tag(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    container_id: str,
    workspace_id: str,
    tag_id: str,
    type: str,
    parameter: str,
    name: str | None = None,
    live_only: bool | None = None,
    notes: str | None = None,
    consent_settings: str | None = None,
    monitoring_metadata: str | None = None,
) -> UpdateTagOutput:
    """Update a tag in a Google Tag Manager workspace."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "type": type,
        "parameter": _safe_json_loads(parameter),
    }
    if name is not None:
        body["name"] = name
    if live_only is not None:
        body["liveOnly"] = live_only
    if notes is not None:
        body["notes"] = notes
    if consent_settings is not None:
        body["consentSettings"] = _safe_json_loads(consent_settings)
    if monitoring_metadata is not None:
        body["monitoringMetadata"] = _safe_json_loads(monitoring_metadata)
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/tags/{tag_id}",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return UpdateTagOutput(success=True, tag=_parse_tag(data))


@tool(args_schema=UpdateVariableInput)
@serialize_pydantic_return
async def update_variable(
    auth_type: str,
    auth_data: dict[str, Any],
    account_id: str,
    container_id: str,
    workspace_id: str,
    variable_id: str,
    name: str,
    type: str,
    parameter: str,
    format_value: str | None = None,
) -> UpdateVariableOutput:
    """Update a variable in a Google Tag Manager workspace."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {
        "name": name,
        "type": type,
        "parameter": _safe_json_loads(parameter),
        "vendorTemplate": {"key": {}},
    }
    if format_value is not None:
        body["formatValue"] = _safe_json_loads(format_value)
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/accounts/{account_id}/containers/{container_id}/workspaces/{workspace_id}/variables/{variable_id}",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return UpdateVariableOutput(success=True, data=data)
