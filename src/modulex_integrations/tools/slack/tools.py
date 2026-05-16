"""Slack LangChain ``@tool`` functions.

Eight async tools wrapping the Slack Web API. Same calling convention
as the github integration: ``auth_type``/``auth_data`` are the first
two parameters and are injected by the modulex ``ToolExecutor``.

**Error handling differs from github**: Slack returns HTTP 200 with
``{"ok": false, "error": "..."}`` instead of HTTP error codes. Each
function inspects ``data["ok"]`` and returns its output model with
``success=False`` + ``error`` set on the failure branch. The success
branch populates the result fields and leaves ``error=None``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations.tools.slack.outputs import (
    AddReactionOutput,
    Channel,
    ChannelMessage,
    GetChannelHistoryOutput,
    GetThreadRepliesOutput,
    GetUserProfileOutput,
    GetUsersOutput,
    ListChannelsOutput,
    Message,
    PostMessageOutput,
    ReplyToThreadOutput,
    ThreadMessage,
    User,
    UserProfile,
)

__all__ = [
    "add_reaction",
    "get_channel_history",
    "get_thread_replies",
    "get_user_profile",
    "get_users",
    "list_channels",
    "post_message",
    "reply_to_thread",
]


# --- Auth helpers ----------------------------------------------------------


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build Slack API headers for the given credential."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    elif auth_type == "bearer_token":
        token = auth_data.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListChannelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    team_id: str | None = Field(default=None, description="Team/workspace ID to filter channels")
    limit: int = Field(default=100, description="Maximum number of channels to return (max 200)")
    cursor: str | None = Field(default=None, description="Pagination cursor for next page")


class PostMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    channel_id: str = Field(description="The ID of the channel to post to")
    text: str = Field(description="The message text to post")


class ReplyToThreadInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    channel_id: str = Field(description="The ID of the channel containing the thread")
    thread_ts: str = Field(
        description="The timestamp of the parent message (format '1234567890.123456')"
    )
    text: str = Field(description="The reply text")


class AddReactionInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    channel_id: str = Field(description="The ID of the channel containing the message")
    timestamp: str = Field(description="The timestamp of the message to react to")
    reaction: str = Field(description="The name of the emoji reaction (without colons)")


class GetChannelHistoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    channel_id: str = Field(description="The ID of the channel")
    limit: int = Field(default=10, description="Number of messages to retrieve")


class GetThreadRepliesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    channel_id: str = Field(description="The ID of the channel containing the thread")
    thread_ts: str = Field(
        description="The timestamp of the parent message (format '1234567890.123456')"
    )


class GetUsersInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    team_id: str | None = Field(default=None, description="Team/workspace ID")
    limit: int = Field(default=100, description="Maximum number of users to return (max 200)")
    cursor: str | None = Field(default=None, description="Pagination cursor for next page")


class GetUserProfileInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    user_id: str = Field(description="The ID of the user")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListChannelsInput)
async def list_channels(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> ListChannelsOutput:
    """List public channels in the Slack workspace with pagination."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "types": "public_channel",
        "exclude_archived": "true",
        "limit": min(limit, 200),
    }
    if team_id:
        params["team_id"] = team_id
    if cursor:
        params["cursor"] = cursor
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.list", headers=headers, params=params
        )
        data = response.json()
    if not data.get("ok"):
        return ListChannelsOutput(success=False, error=data.get("error", "Unknown error"))
    channels = data.get("channels") or []
    return ListChannelsOutput(
        success=True,
        channels=[
            Channel(
                id=ch.get("id"),
                name=ch.get("name"),
                is_channel=ch.get("is_channel"),
                is_private=ch.get("is_private"),
                is_archived=ch.get("is_archived"),
                is_member=ch.get("is_member"),
                num_members=ch.get("num_members"),
                topic=(ch.get("topic") or {}).get("value"),
                purpose=(ch.get("purpose") or {}).get("value"),
                created=ch.get("created"),
            )
            for ch in channels
        ],
        total=len(channels),
        next_cursor=(data.get("response_metadata") or {}).get("next_cursor"),
    )


@tool(args_schema=PostMessageInput)
async def post_message(
    auth_type: str,
    auth_data: dict[str, Any],
    channel_id: str,
    text: str,
) -> PostMessageOutput:
    """Post a new message to a Slack channel."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {"channel": channel_id, "text": text}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage", headers=headers, json=payload
        )
        data = response.json()
    if not data.get("ok"):
        return PostMessageOutput(success=False, error=data.get("error", "Unknown error"))
    message = data.get("message") or {}
    return PostMessageOutput(
        success=True,
        channel=data.get("channel"),
        ts=data.get("ts"),
        message=Message(
            text=message.get("text"),
            user=message.get("user"),
            type=message.get("type"),
            ts=message.get("ts"),
        ),
    )


@tool(args_schema=ReplyToThreadInput)
async def reply_to_thread(
    auth_type: str,
    auth_data: dict[str, Any],
    channel_id: str,
    thread_ts: str,
    text: str,
) -> ReplyToThreadOutput:
    """Reply to a specific message thread in Slack."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {"channel": channel_id, "thread_ts": thread_ts, "text": text}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/chat.postMessage", headers=headers, json=payload
        )
        data = response.json()
    if not data.get("ok"):
        return ReplyToThreadOutput(success=False, error=data.get("error", "Unknown error"))
    message = data.get("message") or {}
    return ReplyToThreadOutput(
        success=True,
        channel=data.get("channel"),
        ts=data.get("ts"),
        thread_ts=thread_ts,
        message=Message(
            text=message.get("text"),
            user=message.get("user"),
            type=message.get("type"),
            ts=message.get("ts"),
        ),
    )


@tool(args_schema=AddReactionInput)
async def add_reaction(
    auth_type: str,
    auth_data: dict[str, Any],
    channel_id: str,
    timestamp: str,
    reaction: str,
) -> AddReactionOutput:
    """Add a reaction emoji to a message."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {"channel": channel_id, "timestamp": timestamp, "name": reaction}
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://slack.com/api/reactions.add", headers=headers, json=payload
        )
        data = response.json()
    if not data.get("ok"):
        return AddReactionOutput(success=False, error=data.get("error", "Unknown error"))
    return AddReactionOutput(
        success=True, channel=channel_id, timestamp=timestamp, reaction=reaction
    )


@tool(args_schema=GetChannelHistoryInput)
async def get_channel_history(
    auth_type: str,
    auth_data: dict[str, Any],
    channel_id: str,
    limit: int = 10,
) -> GetChannelHistoryOutput:
    """Get recent messages from a Slack channel (newest first)."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"channel": channel_id, "limit": limit}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.history", headers=headers, params=params
        )
        data = response.json()
    if not data.get("ok"):
        return GetChannelHistoryOutput(success=False, error=data.get("error", "Unknown error"))
    messages = data.get("messages") or []
    return GetChannelHistoryOutput(
        success=True,
        channel=channel_id,
        messages=[
            ChannelMessage(
                type=m.get("type"),
                user=m.get("user"),
                text=m.get("text"),
                ts=m.get("ts"),
                thread_ts=m.get("thread_ts"),
                reply_count=m.get("reply_count"),
                reactions=m.get("reactions") or [],
            )
            for m in messages
        ],
        total=len(messages),
        has_more=bool(data.get("has_more", False)),
    )


@tool(args_schema=GetThreadRepliesInput)
async def get_thread_replies(
    auth_type: str,
    auth_data: dict[str, Any],
    channel_id: str,
    thread_ts: str,
) -> GetThreadRepliesOutput:
    """Get all replies in a message thread."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"channel": channel_id, "ts": thread_ts}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/conversations.replies", headers=headers, params=params
        )
        data = response.json()
    if not data.get("ok"):
        return GetThreadRepliesOutput(success=False, error=data.get("error", "Unknown error"))
    messages = data.get("messages") or []
    return GetThreadRepliesOutput(
        success=True,
        channel=channel_id,
        thread_ts=thread_ts,
        messages=[
            ThreadMessage(
                type=m.get("type"),
                user=m.get("user"),
                text=m.get("text"),
                ts=m.get("ts"),
                thread_ts=m.get("thread_ts"),
                parent_user_id=m.get("parent_user_id"),
                reactions=m.get("reactions") or [],
            )
            for m in messages
        ],
        total=len(messages),
        has_more=bool(data.get("has_more", False)),
    )


@tool(args_schema=GetUsersInput)
async def get_users(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str | None = None,
    limit: int = 100,
    cursor: str | None = None,
) -> GetUsersOutput:
    """Get a list of all users in the Slack workspace."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"limit": min(limit, 200)}
    if team_id:
        params["team_id"] = team_id
    if cursor:
        params["cursor"] = cursor
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/users.list", headers=headers, params=params
        )
        data = response.json()
    if not data.get("ok"):
        return GetUsersOutput(success=False, error=data.get("error", "Unknown error"))
    members = data.get("members") or []
    return GetUsersOutput(
        success=True,
        users=[
            User(
                id=u.get("id"),
                name=u.get("name"),
                real_name=u.get("real_name"),
                display_name=(u.get("profile") or {}).get("display_name"),
                email=(u.get("profile") or {}).get("email"),
                is_admin=u.get("is_admin"),
                is_owner=u.get("is_owner"),
                is_bot=u.get("is_bot"),
                deleted=u.get("deleted"),
                tz=u.get("tz"),
                updated=u.get("updated"),
            )
            for u in members
        ],
        total=len(members),
        next_cursor=(data.get("response_metadata") or {}).get("next_cursor"),
    )


@tool(args_schema=GetUserProfileInput)
async def get_user_profile(
    auth_type: str,
    auth_data: dict[str, Any],
    user_id: str,
) -> GetUserProfileOutput:
    """Get detailed profile information for a specific user."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"user": user_id, "include_labels": "true"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://slack.com/api/users.profile.get", headers=headers, params=params
        )
        data = response.json()
    if not data.get("ok"):
        return GetUserProfileOutput(success=False, error=data.get("error", "Unknown error"))
    profile = data.get("profile") or {}
    return GetUserProfileOutput(
        success=True,
        user_id=user_id,
        profile=UserProfile(
            real_name=profile.get("real_name"),
            display_name=profile.get("display_name"),
            email=profile.get("email"),
            phone=profile.get("phone"),
            title=profile.get("title"),
            status_text=profile.get("status_text"),
            status_emoji=profile.get("status_emoji"),
            image_24=profile.get("image_24"),
            image_48=profile.get("image_48"),
            image_72=profile.get("image_72"),
            image_192=profile.get("image_192"),
            image_512=profile.get("image_512"),
        ),
    )
