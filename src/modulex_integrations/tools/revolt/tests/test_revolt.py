"""Happy-path tests for every revolt @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.revolt import (
    TOOLS,
    add_group_member,
    create_group,
    manifest,
    send_friend_request,
)
from modulex_integrations.tools.revolt.outputs import (
    AddGroupMemberOutput,
    CreateGroupOutput,
    SendFriendRequestOutput,
)

API = "https://revolt.chat/api"

_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "fake_session_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_3_actions(self) -> None:
        assert len(manifest.actions) == 3

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_bearer_token_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"bearer_token"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_create_group(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/channels/create",
        json={
            # TODO: fill in a representative response shape from the Revolt API docs
            "_id": "01ABCDEF",
            "channel_type": "Group",
            "name": "Test Group",
            "owner": "01USER",
            "nsfw": False,
        },
    )

    result_dict = await create_group.ainvoke(_args(name="Test Group"))

    assert isinstance(result_dict, dict)
    result = CreateGroupOutput.model_validate(result_dict)
    assert result.success is True
    assert result.channel_id == "01ABCDEF"
    assert result.name == "Test Group"


@pytest.mark.asyncio
async def test_add_group_member(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/channels/01GROUP/recipients/01MEMBER",
        status_code=204,
    )

    result_dict = await add_group_member.ainvoke(
        _args(target="01GROUP", member="01MEMBER")
    )

    assert isinstance(result_dict, dict)
    result = AddGroupMemberOutput.model_validate(result_dict)
    assert result.success is True


@pytest.mark.asyncio
async def test_send_friend_request(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/friend",
        json={
            # TODO: fill in a representative response shape from the Revolt API docs
            "_id": "01TARGET",
            "status": "Outgoing",
        },
    )

    result_dict = await send_friend_request.ainvoke(
        _args(username="testuser#0001")
    )

    assert isinstance(result_dict, dict)
    result = SendFriendRequestOutput.model_validate(result_dict)
    assert result.success is True
    assert result.user_id == "01TARGET"
    assert result.status == "Outgoing"


# --- Failure-path tests ----------------------------------------------------


@pytest.mark.asyncio
async def test_create_group_empty_token():  # type: ignore[no-untyped-def]
    """Empty credential should short-circuit without hitting the wire."""
    result_dict = await create_group.ainvoke(
        {"auth_type": "bearer_token", "auth_data": {"token": ""}, "name": "Test"}
    )

    assert isinstance(result_dict, dict)
    result = CreateGroupOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "token" in result.error.lower()
