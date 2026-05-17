"""Microsoft Teams LangChain @tool functions.

All actions are async and call Microsoft Graph v1.0 directly via
``httpx.AsyncClient``. Authentication is OAuth2; the access token is injected
by ModuleX's credential layer as ``auth_data["access_token"]``.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, ConfigDict, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.microsoft_teams.outputs import (
    ChannelResource,
    ChatMessageResource,
    ChatResource,
    CreateChannelOutput,
    CurrentUser,
    GetChatMessageOutput,
    GetCurrentUserOutput,
    ListChannelMessagesOutput,
    ListChannelsOutput,
    ListChatsOutput,
    ListMessagesInChatOutput,
    ListShiftsOutput,
    ListTeamsOutput,
    SearchMessagesOutput,
    SearchResponse,
    SendChannelMessageOutput,
    SendChatMessageOutput,
    ShiftResource,
    TeamResource,
)

__all__ = [
    "create_channel",
    "get_chat_message",
    "get_current_user",
    "list_channel_messages",
    "list_channels",
    "list_chats",
    "list_messages_in_chat",
    "list_shifts",
    "list_teams",
    "search_messages",
    "send_channel_message",
    "send_chat_message",
]

_BASE_URL = "https://graph.microsoft.com/v1.0"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build headers for Microsoft Graph based on the injected credential."""
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


async def _paginate(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    first_url: str,
    max_results: int | None = None,
    max_pages: int = 50,
) -> dict[str, Any]:
    """Walk ``@odata.nextLink`` pages and collect values into a single list.

    Returns ``{"ok": True, "items": [...]}`` on success or
    ``{"ok": False, "status": int, "text": str}`` on error.
    """
    items: list[dict[str, Any]] = []
    next_url: str | None = first_url
    pages_seen = 0
    while next_url and pages_seen < max_pages:
        pages_seen += 1
        response = await client.get(next_url, headers=headers)
        if response.status_code >= 400:
            return {
                "ok": False,
                "status": response.status_code,
                "text": response.text,
            }
        payload = response.json()
        for value in payload.get("value", []) or []:
            items.append(value)
            if max_results is not None and len(items) >= max_results:
                return {"ok": True, "items": items}
        next_url = payload.get("@odata.nextLink")
    return {"ok": True, "items": items}


async def _get_user_id(
    client: httpx.AsyncClient,
    headers: dict[str, str],
) -> str | None:
    """Fetch /me and return the user id, or None on failure."""
    response = await client.get(f"{_BASE_URL}/me", headers=headers)
    if response.status_code >= 400:
        return None
    payload = response.json() or {}
    return payload.get("id")


def _parse_hosted_contents(
    items: list[Any] | None,
) -> list[dict[str, Any]]:
    """Accept either dicts or JSON-string-encoded dicts; return list of dicts."""
    out: list[dict[str, Any]] = []
    if not items:
        return out
    for item in items:
        if isinstance(item, dict):
            out.append(item)
        elif isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, dict):
                    out.append(parsed)
            except json.JSONDecodeError:
                continue
    return out


# --- Input schemas --------------------------------------------------------


class CreateChannelInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    team_id: str = Field(
        description="ID of the Microsoft Team. Obtain it via `list_teams`."
    )
    display_name: str = Field(description="Display name of the channel.")
    description: str | None = Field(
        default=None, description="Description of the channel."
    )


class GetChatMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    chat_id: str = Field(
        description="ID of the chat. Obtain it via `list_chats`."
    )
    message_id: str = Field(
        description=(
            "ID of the message to retrieve. Obtain it via `list_messages_in_chat`."
        )
    )


class GetCurrentUserInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )


class ListChannelMessagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    team_id: str = Field(description="ID of the Microsoft Team.")
    channel_id: str = Field(description="ID of the channel within the team.")
    max_results: int | None = Field(
        default=None,
        description=(
            "The maximum number of messages to return. Omit to fetch all "
            "available pages."
        ),
    )


class ListChannelsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    team_id: str = Field(description="ID of the Microsoft Team.")


class ListChatsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )


class ListMessagesInChatInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    chat_id: str = Field(description="ID of the chat.")
    max_results: int | None = Field(
        default=None,
        description=(
            "The maximum number of results to return. Omit to fetch all "
            "available pages."
        ),
    )


class ListShiftsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    team_id: str = Field(
        description="ID of the Microsoft Team whose schedule is being queried."
    )


class ListTeamsInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )


class SearchMessagesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    entity_type: str = Field(
        description=(
            "The type of entity to search for. `message` for email, "
            "`chatMessage` for Teams chat messages."
        )
    )
    query_string: str = Field(description="The query string to search for.")
    from_: int = Field(
        default=0,
        alias="from",
        description="The index of the first result to return.",
    )
    size: int = Field(
        default=25,
        description="The number of results to return (max 25).",
    )

    model_config = ConfigDict(populate_by_name=True)


class SendChannelMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    team_id: str = Field(description="ID of the Microsoft Team.")
    channel_id: str = Field(description="ID of the channel within the team.")
    message: str = Field(description="Message to be sent.")
    content_type: str | None = Field(
        default="text",
        description=(
            "Whether the message body is plain text or HTML. One of `text`, `html`."
        ),
    )
    hosted_contents: list[str] | None = Field(
        default=None,
        description=(
            "An array of JSON strings, each representing an inline hosted image. "
            "Each item must be a JSON object with `@microsoft.graph.temporaryId` "
            "(string), `contentBytes` (base64-encoded image data), and "
            "`contentType` (MIME type)."
        ),
    )


class SendChatMessageInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2)")
    auth_data: dict[str, Any] = Field(
        description="Authentication data containing the OAuth access token"
    )
    chat_id: str = Field(description="ID of the chat to post the message to.")
    message: str = Field(description="Message to be sent.")
    content_type: str | None = Field(
        default="text",
        description=(
            "Whether the message body is plain text or HTML. One of `text`, `html`."
        ),
    )


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateChannelInput)
@serialize_pydantic_return
async def create_channel(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str,
    display_name: str,
    description: str | None = None,
) -> CreateChannelOutput:
    """Create a new channel in Microsoft Teams."""
    if not auth_data.get("access_token"):
        return CreateChannelOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"displayName": display_name}
    if description is not None:
        payload["description"] = description

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/teams/{quote(team_id)}/channels",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            return CreateChannelOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateChannelOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateChannelOutput(success=False, error=f"Call failed: {exc}")

    return CreateChannelOutput(
        success=True,
        channel=ChannelResource(
            id=data.get("id"),
            displayName=data.get("displayName"),
            description=data.get("description"),
            membershipType=data.get("membershipType"),
            webUrl=data.get("webUrl"),
        ),
    )


@tool(args_schema=GetChatMessageInput)
@serialize_pydantic_return
async def get_chat_message(
    auth_type: str,
    auth_data: dict[str, Any],
    chat_id: str,
    message_id: str,
) -> GetChatMessageOutput:
    """Get a specific message from a chat."""
    if not auth_data.get("access_token"):
        return GetChatMessageOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/chats/{quote(chat_id)}/messages/{quote(message_id)}",
                headers=headers,
            )
        if response.status_code >= 400:
            return GetChatMessageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetChatMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetChatMessageOutput(success=False, error=f"Call failed: {exc}")

    return GetChatMessageOutput(
        success=True,
        message=ChatMessageResource.model_validate(data),
    )


@tool(args_schema=GetCurrentUserInput)
@serialize_pydantic_return
async def get_current_user(
    auth_type: str,
    auth_data: dict[str, Any],
) -> GetCurrentUserOutput:
    """Returns the authenticated Microsoft Teams user's ID, display name, email, and principal name via Microsoft Graph."""
    if not auth_data.get("access_token"):
        return GetCurrentUserOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{_BASE_URL}/me?$select=id,displayName,mail,userPrincipalName",
                headers=headers,
            )
        if response.status_code >= 400:
            return GetCurrentUserOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json() or {}
    except httpx.TimeoutException:
        return GetCurrentUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCurrentUserOutput(success=False, error=f"Call failed: {exc}")

    return GetCurrentUserOutput(
        success=True,
        user=CurrentUser(
            id=data.get("id"),
            displayName=data.get("displayName"),
            mail=data.get("mail"),
            userPrincipalName=data.get("userPrincipalName"),
        ),
    )


@tool(args_schema=ListChannelMessagesInput)
@serialize_pydantic_return
async def list_channel_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str,
    channel_id: str,
    max_results: int | None = None,
) -> ListChannelMessagesOutput:
    """Lists messages in a Microsoft Teams channel."""
    if not auth_data.get("access_token"):
        return ListChannelMessagesOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    first_url = (
        f"{_BASE_URL}/teams/{quote(team_id)}/channels/{quote(channel_id)}/messages"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await _paginate(client, headers, first_url, max_results)
    except httpx.TimeoutException:
        return ListChannelMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListChannelMessagesOutput(success=False, error=f"Call failed: {exc}")

    if not result.get("ok"):
        return ListChannelMessagesOutput(
            success=False,
            error=f"API error ({result.get('status')}): {result.get('text')}",
        )
    return ListChannelMessagesOutput(
        success=True,
        messages=[
            ChatMessageResource.model_validate(item) for item in result["items"]
        ],
    )


@tool(args_schema=ListChannelsInput)
@serialize_pydantic_return
async def list_channels(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str,
) -> ListChannelsOutput:
    """Lists all channels in a Microsoft Team."""
    if not auth_data.get("access_token"):
        return ListChannelsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    first_url = f"{_BASE_URL}/teams/{quote(team_id)}/channels"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await _paginate(client, headers, first_url)
    except httpx.TimeoutException:
        return ListChannelsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListChannelsOutput(success=False, error=f"Call failed: {exc}")

    if not result.get("ok"):
        return ListChannelsOutput(
            success=False,
            error=f"API error ({result.get('status')}): {result.get('text')}",
        )
    return ListChannelsOutput(
        success=True,
        channels=[ChannelResource.model_validate(item) for item in result["items"]],
    )


@tool(args_schema=ListChatsInput)
@serialize_pydantic_return
async def list_chats(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListChatsOutput:
    """Lists all chat conversations for the authenticated user."""
    if not auth_data.get("access_token"):
        return ListChatsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    first_url = f"{_BASE_URL}/chats?$expand=members"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await _paginate(client, headers, first_url)
    except httpx.TimeoutException:
        return ListChatsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListChatsOutput(success=False, error=f"Call failed: {exc}")

    if not result.get("ok"):
        return ListChatsOutput(
            success=False,
            error=f"API error ({result.get('status')}): {result.get('text')}",
        )
    return ListChatsOutput(
        success=True,
        chats=[ChatResource.model_validate(item) for item in result["items"]],
    )


@tool(args_schema=ListMessagesInChatInput)
@serialize_pydantic_return
async def list_messages_in_chat(
    auth_type: str,
    auth_data: dict[str, Any],
    chat_id: str,
    max_results: int | None = None,
) -> ListMessagesInChatOutput:
    """Get the list of messages in a chat."""
    if not auth_data.get("access_token"):
        return ListMessagesInChatOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    first_url = (
        f"{_BASE_URL}/chats/{quote(chat_id)}/messages"
        f"?$orderby=createdDateTime%20desc"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await _paginate(client, headers, first_url, max_results)
    except httpx.TimeoutException:
        return ListMessagesInChatOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListMessagesInChatOutput(success=False, error=f"Call failed: {exc}")

    if not result.get("ok"):
        return ListMessagesInChatOutput(
            success=False,
            error=f"API error ({result.get('status')}): {result.get('text')}",
        )
    return ListMessagesInChatOutput(
        success=True,
        messages=[
            ChatMessageResource.model_validate(item) for item in result["items"]
        ],
    )


@tool(args_schema=ListShiftsInput)
@serialize_pydantic_return
async def list_shifts(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str,
) -> ListShiftsOutput:
    """Get the list of shift instances for a team."""
    if not auth_data.get("access_token"):
        return ListShiftsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    first_url = f"{_BASE_URL}/teams/{quote(team_id)}/schedule/shifts"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            result = await _paginate(client, headers, first_url)
    except httpx.TimeoutException:
        return ListShiftsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListShiftsOutput(success=False, error=f"Call failed: {exc}")

    if not result.get("ok"):
        return ListShiftsOutput(
            success=False,
            error=f"API error ({result.get('status')}): {result.get('text')}",
        )
    return ListShiftsOutput(
        success=True,
        shifts=[ShiftResource.model_validate(item) for item in result["items"]],
    )


@tool(args_schema=ListTeamsInput)
@serialize_pydantic_return
async def list_teams(
    auth_type: str,
    auth_data: dict[str, Any],
) -> ListTeamsOutput:
    """Lists all teams the authenticated user has joined."""
    if not auth_data.get("access_token"):
        return ListTeamsOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            user_id = await _get_user_id(client, headers)
            if not user_id:
                return ListTeamsOutput(
                    success=False,
                    error="Failed to resolve authenticated user id from /me",
                )
            first_url = f"{_BASE_URL}/users/{quote(user_id)}/joinedTeams"
            result = await _paginate(client, headers, first_url)
    except httpx.TimeoutException:
        return ListTeamsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTeamsOutput(success=False, error=f"Call failed: {exc}")

    if not result.get("ok"):
        return ListTeamsOutput(
            success=False,
            error=f"API error ({result.get('status')}): {result.get('text')}",
        )
    return ListTeamsOutput(
        success=True,
        teams=[TeamResource.model_validate(item) for item in result["items"]],
    )


@tool(args_schema=SearchMessagesInput)
@serialize_pydantic_return
async def search_messages(
    auth_type: str,
    auth_data: dict[str, Any],
    entity_type: str,
    query_string: str,
    from_: int = 0,
    size: int = 25,
) -> SearchMessagesOutput:
    """Search for email or chat messages."""
    if not auth_data.get("access_token"):
        return SearchMessagesOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {
        "requests": [
            {
                "entityTypes": [entity_type],
                "query": {"queryString": query_string},
                "from": from_,
                "size": min(size, 25),
            }
        ]
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/search/query",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            return SearchMessagesOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json() or {}
    except httpx.TimeoutException:
        return SearchMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SearchMessagesOutput(success=False, error=f"Call failed: {exc}")

    return SearchMessagesOutput(
        success=True,
        result=SearchResponse.model_validate(data),
    )


@tool(args_schema=SendChannelMessageInput)
@serialize_pydantic_return
async def send_channel_message(
    auth_type: str,
    auth_data: dict[str, Any],
    team_id: str,
    channel_id: str,
    message: str,
    content_type: str | None = "text",
    hosted_contents: list[str] | None = None,
) -> SendChannelMessageOutput:
    """Send a message to a team's channel. Optionally include inline images via `hosted_contents`."""
    if not auth_data.get("access_token"):
        return SendChannelMessageOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    body_block: dict[str, Any] = {
        "body": {
            "content": message,
            "contentType": content_type or "text",
        }
    }
    parsed = _parse_hosted_contents(hosted_contents)
    if parsed:
        body_block["hostedContents"] = parsed

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/teams/{quote(team_id)}/channels/{quote(channel_id)}/messages",
                headers=headers,
                json=body_block,
            )
        if response.status_code >= 400:
            return SendChannelMessageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendChannelMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendChannelMessageOutput(success=False, error=f"Call failed: {exc}")

    return SendChannelMessageOutput(
        success=True,
        message=ChatMessageResource.model_validate(data),
    )


@tool(args_schema=SendChatMessageInput)
@serialize_pydantic_return
async def send_chat_message(
    auth_type: str,
    auth_data: dict[str, Any],
    chat_id: str,
    message: str,
    content_type: str | None = "text",
) -> SendChatMessageOutput:
    """Send a message to a team's chat."""
    if not auth_data.get("access_token"):
        return SendChatMessageOutput(success=False, error="Missing access_token in auth_data.")
    headers = _get_auth_headers(auth_type, auth_data)
    payload = {
        "body": {
            "content": message,
            "contentType": content_type or "text",
        }
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{_BASE_URL}/chats/{quote(chat_id)}/messages",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            return SendChatMessageOutput(
                success=False,
                error=f"API error ({response.status_code}): {response.text}",
            )
        data = response.json()
    except httpx.TimeoutException:
        return SendChatMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendChatMessageOutput(success=False, error=f"Call failed: {exc}")

    return SendChatMessageOutput(
        success=True,
        message=ChatMessageResource.model_validate(data),
    )
