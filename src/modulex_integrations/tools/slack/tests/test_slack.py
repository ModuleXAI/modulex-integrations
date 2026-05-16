"""Happy-path tests + one failure case per error-handling regime.

Slack returns HTTP 200 with ``ok: false`` on errors. We test:

- 8 happy-path tests (one per @tool) — assert ``success=True`` and
  representative output fields populate correctly.
- 1 failure-path test (``post_message`` with ``ok: false``) — asserts
  the Slack-specific ``success=False`` + ``error`` branch works.
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.slack import (
    TOOLS,
    add_reaction,
    get_channel_history,
    get_thread_replies,
    get_user_profile,
    get_users,
    list_channels,
    manifest,
    post_message,
    reply_to_thread,
)
from modulex_integrations.tools.slack.outputs import (
    AddReactionOutput,
    GetChannelHistoryOutput,
    GetThreadRepliesOutput,
    GetUserProfileOutput,
    GetUsersOutput,
    ListChannelsOutput,
    PostMessageOutput,
    ReplyToThreadOutput,
)

API = "https://slack.com/api"
_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "xoxb-fake-token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2", "bearer_token"}


# --- Happy-path tests ------------------------------------------------------


@pytest.mark.asyncio
async def test_list_channels(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations.list?types=public_channel&exclude_archived=true&limit=100",
        json={
            "ok": True,
            "channels": [
                {
                    "id": "C100",
                    "name": "general",
                    "is_channel": True,
                    "is_private": False,
                    "is_archived": False,
                    "is_member": True,
                    "num_members": 12,
                    "topic": {"value": "company-wide chat"},
                    "purpose": {"value": "general"},
                    "created": 1700000000,
                }
            ],
            "response_metadata": {"next_cursor": ""},
        },
    )

    result = await list_channels.ainvoke(_AUTH)

    assert isinstance(result, ListChannelsOutput)
    assert result.success is True
    assert result.channels[0].id == "C100"
    assert result.channels[0].topic == "company-wide chat"
    assert result.total == 1


@pytest.mark.asyncio
async def test_post_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/chat.postMessage",
        json={
            "ok": True,
            "channel": "C100",
            "ts": "1700000000.000001",
            "message": {
                "text": "hello",
                "user": "U100",
                "type": "message",
                "ts": "1700000000.000001",
            },
        },
    )

    result = await post_message.ainvoke(_args(channel_id="C100", text="hello"))

    assert isinstance(result, PostMessageOutput)
    assert result.success is True
    assert result.ts == "1700000000.000001"
    assert result.message is not None
    assert result.message.text == "hello"


@pytest.mark.asyncio
async def test_reply_to_thread(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/chat.postMessage",
        json={
            "ok": True,
            "channel": "C100",
            "ts": "1700000000.000002",
            "message": {
                "text": "reply",
                "user": "U101",
                "type": "message",
                "ts": "1700000000.000002",
            },
        },
    )

    result = await reply_to_thread.ainvoke(
        _args(channel_id="C100", thread_ts="1700000000.000001", text="reply")
    )

    assert isinstance(result, ReplyToThreadOutput)
    assert result.success is True
    assert result.thread_ts == "1700000000.000001"
    assert result.message is not None
    assert result.message.text == "reply"


@pytest.mark.asyncio
async def test_add_reaction(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/reactions.add",
        json={"ok": True},
    )

    result = await add_reaction.ainvoke(
        _args(channel_id="C100", timestamp="1700000000.000001", reaction="thumbsup")
    )

    assert isinstance(result, AddReactionOutput)
    assert result.success is True
    assert result.reaction == "thumbsup"


@pytest.mark.asyncio
async def test_get_channel_history(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations.history?channel=C100&limit=10",
        json={
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U100",
                    "text": "first",
                    "ts": "1700000000.000001",
                    "thread_ts": None,
                    "reply_count": None,
                    "reactions": None,
                }
            ],
            "has_more": False,
        },
    )

    result = await get_channel_history.ainvoke(_args(channel_id="C100"))

    assert isinstance(result, GetChannelHistoryOutput)
    assert result.success is True
    assert result.messages[0].text == "first"
    assert result.has_more is False


@pytest.mark.asyncio
async def test_get_thread_replies(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations.replies?channel=C100&ts=1700000000.000001",
        json={
            "ok": True,
            "messages": [
                {
                    "type": "message",
                    "user": "U100",
                    "text": "parent",
                    "ts": "1700000000.000001",
                    "thread_ts": "1700000000.000001",
                    "parent_user_id": None,
                    "reactions": None,
                },
                {
                    "type": "message",
                    "user": "U101",
                    "text": "reply",
                    "ts": "1700000000.000002",
                    "thread_ts": "1700000000.000001",
                    "parent_user_id": "U100",
                    "reactions": None,
                },
            ],
            "has_more": False,
        },
    )

    result = await get_thread_replies.ainvoke(
        _args(channel_id="C100", thread_ts="1700000000.000001")
    )

    assert isinstance(result, GetThreadRepliesOutput)
    assert result.success is True
    assert len(result.messages) == 2
    assert result.messages[1].parent_user_id == "U100"


@pytest.mark.asyncio
async def test_get_users(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users.list?limit=100",
        json={
            "ok": True,
            "members": [
                {
                    "id": "U100",
                    "name": "alice",
                    "real_name": "Alice Smith",
                    "profile": {"display_name": "Alice", "email": "alice@example.com"},
                    "is_admin": True,
                    "is_owner": False,
                    "is_bot": False,
                    "deleted": False,
                    "tz": "America/Los_Angeles",
                    "updated": 1700000000,
                }
            ],
            "response_metadata": {"next_cursor": "cursor-1"},
        },
    )

    result = await get_users.ainvoke(_AUTH)

    assert isinstance(result, GetUsersOutput)
    assert result.success is True
    assert result.users[0].email == "alice@example.com"
    assert result.users[0].display_name == "Alice"
    assert result.next_cursor == "cursor-1"


@pytest.mark.asyncio
async def test_get_user_profile(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users.profile.get?user=U100&include_labels=true",
        json={
            "ok": True,
            "profile": {
                "real_name": "Alice Smith",
                "display_name": "Alice",
                "email": "alice@example.com",
                "title": "Engineer",
                "image_72": "https://example.com/avatar_72.png",
            },
        },
    )

    result = await get_user_profile.ainvoke(_args(user_id="U100"))

    assert isinstance(result, GetUserProfileOutput)
    assert result.success is True
    assert result.profile is not None
    assert result.profile.title == "Engineer"
    assert result.profile.image_72 == "https://example.com/avatar_72.png"


# --- Failure-path test (exercises the Slack ok:false branch) ----------------


@pytest.mark.asyncio
async def test_post_message_returns_error_on_slack_failure(httpx_mock):  # type: ignore[no-untyped-def]
    """Slack returns HTTP 200 with ok:false on errors; our output model
    propagates that as ``success=False`` + ``error`` rather than raising."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/chat.postMessage",
        json={"ok": False, "error": "channel_not_found"},
    )

    result = await post_message.ainvoke(_args(channel_id="C999", text="hi"))

    assert isinstance(result, PostMessageOutput)
    assert result.success is False
    assert result.error == "channel_not_found"
    assert result.message is None
