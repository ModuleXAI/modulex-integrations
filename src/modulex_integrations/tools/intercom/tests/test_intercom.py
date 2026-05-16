"""Tests for the Intercom integration."""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.intercom import (
    TOOLS,
    add_tag_to_contact,
    create_note,
    get_contact,
    get_conversation,
    list_admins,
    list_conversations,
    list_tags,
    manifest,
    reply_to_conversation,
    search_contacts,
    search_conversations,
    send_incoming_message,
    send_message_to_contact,
    upsert_contact,
)
from modulex_integrations.tools.intercom.outputs import (
    AddTagToContactOutput,
    CreateNoteOutput,
    GetContactOutput,
    GetConversationOutput,
    ListAdminsOutput,
    ListConversationsOutput,
    ListTagsOutput,
    ReplyToConversationOutput,
    SearchContactsOutput,
    SearchConversationsOutput,
    SendIncomingMessageOutput,
    SendMessageToContactOutput,
    UpsertContactOutput,
)

API = "https://api.intercom.io"

_OAUTH_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "ic-oauth-token"},
}
_PAT_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "ic-pat-token"},
}


def _args(auth: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return dict(auth, **extra)


class TestManifest:
    def test_manifest_exposes_thirteen_actions(self) -> None:
        assert len(manifest.actions) == 13

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_paired_oauth2_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}


@pytest.mark.asyncio
async def test_get_contact_oauth(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/C1",
        json={"id": "C1", "email": "a@x.io", "name": "Ada"},
    )
    result_dict = await get_contact.ainvoke(_args(_OAUTH_AUTH, contact_id="C1"))
    assert isinstance(result_dict, dict)
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.result is not None
    assert result.result["email"] == "a@x.io"


@pytest.mark.asyncio
async def test_get_contact_bearer(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/C1",
        json={"id": "C1", "email": "a@x.io"},
    )
    result = GetContactOutput.model_validate(
        await get_contact.ainvoke(_args(_PAT_AUTH, contact_id="C1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_contact_missing_token_validates() -> None:
    bad_auth = {"auth_type": "oauth2", "auth_data": {}}
    result = GetContactOutput.model_validate(
        await get_contact.ainvoke(dict(bad_auth, contact_id="C1"))
    )
    assert result.success is False
    assert result.error is not None and "access token" in result.error


@pytest.mark.asyncio
async def test_search_contacts(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/search",
        json={
            "data": [{"id": "C1", "email": "a@x.io"}, {"id": "C2", "email": "b@x.io"}],
            "total_count": 2,
            "pages": {"page": 1, "per_page": 50, "total_pages": 1},
        },
    )
    result = SearchContactsOutput.model_validate(
        await search_contacts.ainvoke(_args(_OAUTH_AUTH, query_value="a@x.io"))
    )
    assert result.success is True
    assert result.total_count == 2
    assert {c["id"] for c in result.contacts} == {"C1", "C2"}


@pytest.mark.asyncio
async def test_upsert_contact_creates_new(httpx_mock: Any) -> None:
    # 1st call: search returns empty → upsert path takes the "create" branch.
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/search",
        json={"data": [], "total_count": 0},
    )
    # 2nd call: POST /contacts to create
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts",
        status_code=201,
        json={"id": "C99", "email": "new@x.io", "name": "New"},
    )
    result = UpsertContactOutput.model_validate(
        await upsert_contact.ainvoke(_args(_OAUTH_AUTH, email="new@x.io", name="New"))
    )
    assert result.success is True
    assert result.action_type == "created"
    assert result.contact is not None
    assert result.contact["id"] == "C99"


@pytest.mark.asyncio
async def test_upsert_contact_updates_existing(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/search",
        json={"data": [{"id": "C42", "email": "a@x.io"}], "total_count": 1},
    )
    httpx_mock.add_response(
        method="PUT",
        url=f"{API}/contacts/C42",
        json={"id": "C42", "email": "a@x.io", "name": "Ada Lovelace"},
    )
    result = UpsertContactOutput.model_validate(
        await upsert_contact.ainvoke(
            _args(_OAUTH_AUTH, email="a@x.io", name="Ada Lovelace")
        )
    )
    assert result.success is True
    assert result.action_type == "updated"
    assert result.contact is not None
    assert result.contact["name"] == "Ada Lovelace"


@pytest.mark.asyncio
async def test_create_note_uses_me_admin(httpx_mock: Any) -> None:
    httpx_mock.add_response(method="GET", url=f"{API}/me", json={"id": "A1"})
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/C1/notes",
        status_code=201,
        json={"id": "N1", "body": "hello"},
    )
    result = CreateNoteOutput.model_validate(
        await create_note.ainvoke(_args(_OAUTH_AUTH, contact_id="C1", body="hello"))
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["id"] == "N1"


@pytest.mark.asyncio
async def test_create_note_propagates_me_failure(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET", url=f"{API}/me", status_code=401, text="unauthorized"
    )
    result = CreateNoteOutput.model_validate(
        await create_note.ainvoke(_args(_OAUTH_AUTH, contact_id="C1", body="x"))
    )
    assert result.success is False
    assert result.error is not None and "admin" in result.error


@pytest.mark.asyncio
async def test_add_tag_to_contact(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/contacts/C1/tags",
        status_code=201,
        json={"id": "T1", "type": "tag", "name": "vip"},
    )
    result = AddTagToContactOutput.model_validate(
        await add_tag_to_contact.ainvoke(_args(_OAUTH_AUTH, contact_id="C1", tag_id="T1"))
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["name"] == "vip"


@pytest.mark.asyncio
async def test_list_tags(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/tags",
        json={"type": "list", "data": [{"id": "T1", "name": "vip"}]},
    )
    result = ListTagsOutput.model_validate(await list_tags.ainvoke(_args(_OAUTH_AUTH)))
    assert result.success is True
    assert result.result is not None
    assert result.result["data"][0]["name"] == "vip"


@pytest.mark.asyncio
async def test_list_admins(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/admins",
        json={"type": "list", "admins": [{"id": "A1", "name": "Admin"}]},
    )
    result = ListAdminsOutput.model_validate(
        await list_admins.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_get_conversation(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations/CV1",
        json={"id": "CV1", "state": "open"},
    )
    result = GetConversationOutput.model_validate(
        await get_conversation.ainvoke(_args(_OAUTH_AUTH, conversation_id="CV1"))
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["state"] == "open"


@pytest.mark.asyncio
async def test_list_conversations(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations?per_page=20",
        json={
            "conversations": [{"id": "CV1"}, {"id": "CV2"}],
            "pages": {"next": "cursor-xyz"},
        },
    )
    result = ListConversationsOutput.model_validate(
        await list_conversations.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True
    assert len(result.conversations) == 2
    assert result.pages == {"next": "cursor-xyz"}


@pytest.mark.asyncio
async def test_search_conversations(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/conversations/search",
        json={
            "conversations": [{"id": "CV1", "state": "open"}],
            "total_count": 1,
            "pages": {"page": 1, "per_page": 20, "total_pages": 1},
        },
    )
    result = SearchConversationsOutput.model_validate(
        await search_conversations.ainvoke(_args(_OAUTH_AUTH, query_value="1700000000"))
    )
    assert result.success is True
    assert result.total_count == 1


@pytest.mark.asyncio
async def test_send_incoming_message_auto_role(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/C1",
        json={"id": "C1", "role": "lead"},
    )
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/conversations",
        status_code=201,
        json={"id": "CV99", "conversation_id": "CV99"},
    )
    result = SendIncomingMessageOutput.model_validate(
        await send_incoming_message.ainvoke(
            _args(_OAUTH_AUTH, contact_id="C1", body="Hello")
        )
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["id"] == "CV99"


@pytest.mark.asyncio
async def test_send_message_to_contact(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/messages",
        status_code=201,
        json={"id": "M1", "subject": "Hi", "body": "Hello"},
    )
    result = SendMessageToContactOutput.model_validate(
        await send_message_to_contact.ainvoke(
            _args(
                _OAUTH_AUTH,
                from_admin_id="A1",
                to_contact_id="C1",
                subject="Hi",
                body="Hello",
            )
        )
    )
    assert result.success is True
    assert result.result is not None
    assert result.result["id"] == "M1"


@pytest.mark.asyncio
async def test_reply_to_conversation_admin(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/conversations/CV1/parts",
        status_code=200,
        json={"id": "CV1", "state": "open"},
    )
    result = ReplyToConversationOutput.model_validate(
        await reply_to_conversation.ainvoke(
            _args(
                _OAUTH_AUTH,
                conversation_id="CV1",
                reply_type="admin",
                body="Thanks!",
                admin_id="A1",
            )
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_reply_to_conversation_clamps_attachments(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(200, json={"id": "CV1"})

    httpx_mock.add_callback(_capture, method="POST", url=f"{API}/conversations/CV1/parts")
    too_many = [f"https://img/{i}.png" for i in range(15)]
    result = ReplyToConversationOutput.model_validate(
        await reply_to_conversation.ainvoke(
            _args(
                _OAUTH_AUTH,
                conversation_id="CV1",
                reply_type="admin",
                body="x",
                admin_id="A1",
                attachment_urls=too_many,
            )
        )
    )
    assert result.success is True
    assert len(captured["attachment_urls"]) == 10
