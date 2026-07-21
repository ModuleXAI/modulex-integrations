"""Google Tag Manager LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.google_tag_manager.outputs import (
    AccountItem,
    GetTagOutput,
    GetTagsOutput,
    ListAccountIdOptionsOutput,
    TagResource,
)

__all__ = [
    "get_tag",
    "get_tags",
    "list_account_id_options",
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


# --- Input schemas --------------------------------------------------------


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


# --- @tool functions ------------------------------------------------------


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
