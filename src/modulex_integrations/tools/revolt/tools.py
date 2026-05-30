"""Revolt LangChain @tool functions."""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.revolt.outputs import (
    AddGroupMemberOutput,
    CreateGroupOutput,
    SendFriendRequestOutput,
)

__all__ = [
    "add_group_member",
    "create_group",
    "send_friend_request",
]

_BASE_URL = "https://revolt.chat/api"
_TIMEOUT = 30.0


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for the Revolt API using the session token."""
    token = auth_data.get("token", "")
    return {
        "x-session-token": token,
        "Content-Type": "application/json",
    }


# --- Input schemas --------------------------------------------------------


class CreateGroupInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="The name of the group")
    description: str | None = Field(default=None, description="Group description")
    users: list[str] | None = Field(
        default=None, description="IDs of the users to add to the group"
    )
    nsfw: bool | None = Field(default=None, description="Whether this group is age-restricted")


class AddGroupMemberInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    target: str = Field(description="ID of the group channel")
    member: str = Field(description="ID of the user to add")


class SendFriendRequestInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    username: str = Field(description="Username and discriminator combo separated by #")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateGroupInput)
@serialize_pydantic_return
async def create_group(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    description: str | None = None,
    users: list[str] | None = None,
    nsfw: bool | None = None,
) -> CreateGroupOutput:
    """Create a new group channel."""
    token = auth_data.get("token", "")
    if not token or not token.strip():
        return CreateGroupOutput(success=False, error="Missing or empty session token.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"name": name}
    if description is not None:
        payload["description"] = description
    if users is not None:
        payload["users"] = users
    if nsfw is not None:
        payload["nsfw"] = nsfw

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/channels/create",
                headers=headers,
                json=payload,
            )
        if response.status_code not in (200, 201):
            return CreateGroupOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateGroupOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateGroupOutput(success=False, error=f"Call failed: {exc}")

    return CreateGroupOutput(
        success=True,
        channel_id=data.get("_id"),
        channel_type=data.get("channel_type"),
        name=data.get("name"),
        description=data.get("description"),
        owner=data.get("owner"),
        nsfw=data.get("nsfw"),
    )


@tool(args_schema=AddGroupMemberInput)
@serialize_pydantic_return
async def add_group_member(
    auth_type: str,
    auth_data: dict[str, Any],
    target: str,
    member: str,
) -> AddGroupMemberOutput:
    """Add another user to a group channel."""
    token = auth_data.get("token", "")
    if not token or not token.strip():
        return AddGroupMemberOutput(success=False, error="Missing or empty session token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.put(
                f"{_BASE_URL}/channels/{target}/recipients/{member}",
                headers=headers,
            )
        if response.status_code not in (200, 204):
            return AddGroupMemberOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
    except httpx.TimeoutException:
        return AddGroupMemberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddGroupMemberOutput(success=False, error=f"Call failed: {exc}")

    return AddGroupMemberOutput(success=True)


@tool(args_schema=SendFriendRequestInput)
@serialize_pydantic_return
async def send_friend_request(
    auth_type: str,
    auth_data: dict[str, Any],
    username: str,
) -> SendFriendRequestOutput:
    """Send a friend request to another user."""
    token = auth_data.get("token", "")
    if not token or not token.strip():
        return SendFriendRequestOutput(success=False, error="Missing or empty session token.")
    headers = _get_auth_headers(auth_type, auth_data)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/users/friend",
                headers=headers,
                json={"username": username},
            )
        if response.status_code not in (200, 201):
            return SendFriendRequestOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendFriendRequestOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendFriendRequestOutput(success=False, error=f"Call failed: {exc}")

    return SendFriendRequestOutput(
        success=True,
        user_id=data.get("_id"),
        status=data.get("status"),
    )
