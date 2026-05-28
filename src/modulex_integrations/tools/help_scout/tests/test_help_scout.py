"""Happy-path tests for every help_scout @tool, plus a manifest sanity check."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.help_scout import (
    TOOLS,
    add_note,
    create_customer,
    get_conversation_details,
    get_conversation_threads,
    get_tag_by_id,
    list_tags,
    manifest,
    send_reply,
    update_conversation,
)
from modulex_integrations.tools.help_scout.outputs import (
    AddNoteOutput,
    CreateCustomerOutput,
    GetConversationDetailsOutput,
    GetConversationThreadsOutput,
    GetTagByIdOutput,
    ListTagsOutput,
    SendReplyOutput,
    UpdateConversationOutput,
)

API = "https://api.helpscout.net/v2"

_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "fake_access_token"},
}


def _args(**extra: Any) -> dict[str, Any]:
    """Build a ``.ainvoke()`` input dict: auth + per-test extras."""
    return dict(_AUTH, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_8_actions(self) -> None:
        assert len(manifest.actions) == 8

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"oauth2"}


# --- Per-action happy-path tests -------------------------------------------


@pytest.mark.asyncio
async def test_add_note(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/conversations/123/notes",
        status_code=201,
        text="",
    )

    result_dict = await add_note.ainvoke(_args(conversation_id="123", text="A note"))

    assert isinstance(result_dict, dict)
    result = AddNoteOutput.model_validate(result_dict)
    assert result.success is True
    assert result.conversation_id == "123"


@pytest.mark.asyncio
async def test_create_customer(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/customers",
        status_code=201,
        text="",
        headers={"Resource-Id": "456"},
    )

    result_dict = await create_customer.ainvoke(_args(first_name="Jane", last_name="Doe"))

    assert isinstance(result_dict, dict)
    result = CreateCustomerOutput.model_validate(result_dict)
    assert result.success is True
    assert result.customer_id == "456"


@pytest.mark.asyncio
async def test_get_conversation_details(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations/789",
        json={
            "id": 789,
            "number": 100,
            "subject": "Test Subject",
            "status": "active",
            "mailboxId": 1,
            "primaryCustomer": {"id": 10, "email": "test@example.com"},
            "tags": [],
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": "2024-01-02T00:00:00Z",
            # TODO: fill in a more complete response shape from upstream API docs
        },
    )

    result_dict = await get_conversation_details.ainvoke(_args(conversation_id="789"))

    assert isinstance(result_dict, dict)
    result = GetConversationDetailsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.conversation is not None
    assert result.conversation.id == 789
    assert result.conversation.subject == "Test Subject"


@pytest.mark.asyncio
async def test_get_conversation_threads(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations/789/threads?page=1",
        json={
            "_embedded": {
                "threads": [
                    {
                        "id": 1,
                        "type": "customer",
                        "status": "active",
                        "state": "published",
                        "body": "Hello",
                        "createdAt": "2024-01-01T00:00:00Z",
                    },
                ],
            },
            "page": {
                "size": 25,
                "totalElements": 1,
                "totalPages": 1,
                "number": 1,
            },
        },
    )

    result_dict = await get_conversation_threads.ainvoke(_args(conversation_id="789"))

    assert isinstance(result_dict, dict)
    result = GetConversationThreadsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.threads) == 1
    assert result.threads[0].body == "Hello"
    assert result.pagination is not None
    assert result.pagination.total_elements == 1


@pytest.mark.asyncio
async def test_get_tag_by_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tags/42",
        json={
            "id": 42,
            "name": "urgent",
            "slug": "urgent",
            "color": "#FF0000",
            "createdAt": "2024-01-01T00:00:00Z",
            "updatedAt": None,
            "ticketCount": 5,
        },
    )

    result_dict = await get_tag_by_id.ainvoke(_args(tag_id="42"))

    assert isinstance(result_dict, dict)
    result = GetTagByIdOutput.model_validate(result_dict)
    assert result.success is True
    assert result.tag is not None
    assert result.tag.name == "urgent"
    assert result.tag.ticket_count == 5


@pytest.mark.asyncio
async def test_list_tags(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tags?page=1",
        json={
            "_embedded": {
                "tags": [
                    {
                        "id": 1,
                        "name": "bug",
                        "slug": "bug",
                        "color": "#FF0000",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "ticketCount": 10,
                    },
                ],
            },
            "page": {
                "size": 50,
                "totalElements": 1,
                "totalPages": 1,
                "number": 1,
            },
        },
    )

    result_dict = await list_tags.ainvoke(_args())

    assert isinstance(result_dict, dict)
    result = ListTagsOutput.model_validate(result_dict)
    assert result.success is True
    assert len(result.tags) == 1
    assert result.tags[0].name == "bug"


@pytest.mark.asyncio
async def test_send_reply(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/conversations/123/reply",
        status_code=201,
        text="",
    )

    result_dict = await send_reply.ainvoke(
        _args(conversation_id="123", customer_id="456", text="Reply text", draft=False)
    )

    assert isinstance(result_dict, dict)
    result = SendReplyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.conversation_id == "123"


@pytest.mark.asyncio
async def test_update_conversation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/conversations/123",
        status_code=204,
        text="",
    )

    result_dict = await update_conversation.ainvoke(
        _args(conversation_id="123", operation="Change subject", value="New Subject")
    )

    assert isinstance(result_dict, dict)
    result = UpdateConversationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.conversation_id == "123"


# --- Failure-path test ----------------------------------------------------


@pytest.mark.asyncio
async def test_add_note_missing_credential():  # type: ignore[no-untyped-def]
    """Empty credential returns error without hitting the wire."""
    result_dict = await add_note.ainvoke(
        _args(auth_data={}, conversation_id="123", text="A note")
    )

    assert isinstance(result_dict, dict)
    result = AddNoteOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "access token" in result.error.lower()
