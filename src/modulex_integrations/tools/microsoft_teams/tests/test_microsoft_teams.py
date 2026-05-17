"""Happy-path tests for every microsoft_teams @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.microsoft_teams import (
    TOOLS,
    create_channel,
    get_chat_message,
    get_current_user,
    list_channel_messages,
    list_channels,
    list_chats,
    list_messages_in_chat,
    list_shifts,
    list_teams,
    manifest,
    search_messages,
    send_channel_message,
    send_chat_message,
)
from modulex_integrations.tools.microsoft_teams.outputs import (
    CreateChannelOutput,
    GetChatMessageOutput,
    GetCurrentUserOutput,
    ListChannelMessagesOutput,
    ListChannelsOutput,
    ListChatsOutput,
    ListMessagesInChatOutput,
    ListShiftsOutput,
    ListTeamsOutput,
    SearchMessagesOutput,
    SendChannelMessageOutput,
    SendChatMessageOutput,
)

API = "https://graph.microsoft.com/v1.0"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_12_actions(self) -> None:
        assert len(manifest.actions) == 12

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_channel(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/teams/team-1/channels",
        json={
            # TODO: replace with a representative Microsoft Graph Channel resource.
            "id": "19:abc@thread.tacv2",
            "displayName": "New Channel",
            "description": "test channel",
            "membershipType": "standard",
            "webUrl": "https://teams.microsoft.com/l/channel/...",
        },
    )

    result_dict = await create_channel.ainvoke(
        _args(team_id="team-1", display_name="New Channel", description="test channel")
    )

    assert isinstance(result_dict, dict)
    result = CreateChannelOutput.model_validate(result_dict)
    assert result.success is True
    assert result.channel is not None
    # TODO: assert representative channel fields.


@pytest.mark.asyncio
async def test_get_chat_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/chats/chat-1/messages/msg-1",
        json={
            # TODO: replace with a representative Microsoft Graph chatMessage resource.
            "id": "msg-1",
            "createdDateTime": "2024-01-01T00:00:00Z",
            "from": {"user": {"id": "u1"}},
            "body": {"content": "hi", "contentType": "text"},
            "importance": "normal",
            "webUrl": "https://teams.microsoft.com/l/message/...",
        },
    )

    result_dict = await get_chat_message.ainvoke(
        _args(chat_id="chat-1", message_id="msg-1")
    )

    assert isinstance(result_dict, dict)
    result = GetChatMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message is not None


@pytest.mark.asyncio
async def test_get_current_user(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me?$select=id,displayName,mail,userPrincipalName",
        json={
            # TODO: replace with a representative /me payload from Microsoft Graph.
            "id": "user-1",
            "displayName": "Test User",
            "mail": "user@example.com",
            "userPrincipalName": "user@example.onmicrosoft.com",
        },
    )

    result_dict = await get_current_user.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user is not None
    assert result.user.id == "user-1"


@pytest.mark.asyncio
async def test_list_channel_messages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/teams/team-1/channels/chan-1/messages",
        json={
            # TODO: replace with a representative Microsoft Graph /messages list payload.
            "value": [
                {
                    "id": "msg-1",
                    "createdDateTime": "2024-01-01T00:00:00Z",
                    "from": {"user": {"id": "u1"}},
                    "body": {"content": "hello", "contentType": "text"},
                    "webUrl": "https://teams.microsoft.com/l/message/...",
                }
            ],
        },
    )

    result_dict = await list_channel_messages.ainvoke(
        _args(team_id="team-1", channel_id="chan-1")
    )

    assert isinstance(result_dict, dict)
    result = ListChannelMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.messages) >= 1


@pytest.mark.asyncio
async def test_list_channels(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/teams/team-1/channels",
        json={
            # TODO: replace with a representative /channels list payload.
            "value": [
                {
                    "id": "chan-1",
                    "displayName": "General",
                    "description": "general",
                    "membershipType": "standard",
                    "webUrl": "https://teams.microsoft.com/l/channel/...",
                }
            ],
        },
    )

    result_dict = await list_channels.ainvoke(_args(team_id="team-1"))

    assert isinstance(result_dict, dict)
    result = ListChannelsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.channels) >= 1


@pytest.mark.asyncio
async def test_list_chats(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/chats?$expand=members",
        json={
            # TODO: replace with a representative /chats list payload (with members expanded).
            "value": [
                {
                    "id": "chat-1",
                    "topic": "Standup",
                    "chatType": "group",
                    "createdDateTime": "2024-01-01T00:00:00Z",
                    "lastUpdatedDateTime": "2024-01-02T00:00:00Z",
                    "webUrl": "https://teams.microsoft.com/l/chat/...",
                    "members": [],
                }
            ],
        },
    )

    result_dict = await list_chats.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListChatsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_messages_in_chat(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/chats/chat-1/messages?$orderby=createdDateTime%20desc",
        json={
            # TODO: replace with a representative chat /messages list payload.
            "value": [
                {
                    "id": "msg-1",
                    "createdDateTime": "2024-01-01T00:00:00Z",
                    "from": {"user": {"id": "u1"}},
                    "body": {"content": "hi", "contentType": "text"},
                    "webUrl": "https://teams.microsoft.com/l/message/...",
                }
            ],
        },
    )

    result_dict = await list_messages_in_chat.ainvoke(_args(chat_id="chat-1"))

    assert isinstance(result_dict, dict)
    result = ListMessagesInChatOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_shifts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/teams/team-1/schedule/shifts",
        json={
            # TODO: replace with a representative Microsoft Graph /schedule/shifts payload.
            "value": [
                {
                    "id": "shift-1",
                    "userId": "user-1",
                    "schedulingGroupId": "group-1",
                    "createdDateTime": "2024-01-01T00:00:00Z",
                    "lastModifiedDateTime": "2024-01-01T00:00:00Z",
                    "sharedShift": {},
                    "draftShift": {},
                }
            ],
        },
    )

    result_dict = await list_shifts.ainvoke(_args(team_id="team-1"))

    assert isinstance(result_dict, dict)
    result = ListShiftsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_list_teams(httpx_mock):  # type: ignore[no-untyped-def]
    # First, the /me lookup needed to resolve user id.
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/me",
        json={
            # TODO: replace with a representative /me payload.
            "id": "user-1",
        },
    )
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/user-1/joinedTeams",
        json={
            # TODO: replace with a representative joinedTeams payload.
            "value": [
                {
                    "id": "team-1",
                    "displayName": "Engineering",
                    "description": "Eng team",
                    "visibility": "private",
                    "webUrl": "https://teams.microsoft.com/l/team/...",
                }
            ],
        },
    )

    result_dict = await list_teams.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTeamsOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_search_messages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/search/query",
        json={
            # TODO: replace with a representative Microsoft Graph search response.
            "value": [
                {
                    "searchTerms": ["hello"],
                    "hitsContainers": [
                        {
                            "total": 1,
                            "moreResultsAvailable": False,
                            "hits": [],
                        }
                    ],
                }
            ],
        },
    )

    result_dict = await search_messages.ainvoke(
        _args(entity_type="chatMessage", query_string="hello")
    )

    assert isinstance(result_dict, dict)
    result = SearchMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result is not None


@pytest.mark.asyncio
async def test_send_channel_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/teams/team-1/channels/chan-1/messages",
        json={
            # TODO: replace with a representative chatMessage POST response.
            "id": "msg-1",
            "createdDateTime": "2024-01-01T00:00:00Z",
            "from": {"user": {"id": "user-1"}},
            "body": {"content": "hello", "contentType": "text"},
            "webUrl": "https://teams.microsoft.com/l/message/...",
        },
    )

    result_dict = await send_channel_message.ainvoke(
        _args(team_id="team-1", channel_id="chan-1", message="hello")
    )

    assert isinstance(result_dict, dict)
    result = SendChannelMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message is not None


@pytest.mark.asyncio
async def test_send_chat_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/chats/chat-1/messages",
        json={
            # TODO: replace with a representative chatMessage POST response.
            "id": "msg-1",
            "createdDateTime": "2024-01-01T00:00:00Z",
            "from": {"user": {"id": "user-1"}},
            "body": {"content": "hi", "contentType": "text"},
            "webUrl": "https://teams.microsoft.com/l/message/...",
        },
    )

    result_dict = await send_chat_message.ainvoke(
        _args(chat_id="chat-1", message="hi")
    )

    assert isinstance(result_dict, dict)
    result = SendChatMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message is not None


@pytest.mark.asyncio
async def test_get_current_user_empty_credential() -> None:
    """Failure path: missing access_token returns success=False immediately."""
    result_dict = await get_current_user.ainvoke(
        {"auth_type": "oauth2", "auth_data": {}}
    )
    assert isinstance(result_dict, dict)
    result = GetCurrentUserOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access_token" in result.error.lower()
