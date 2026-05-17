"""Tests for the Gmail integration."""
from __future__ import annotations

import base64
from typing import Any

import pytest

from modulex_integrations.tools.gmail import (
    TOOLS,
    add_label,
    archive_message,
    create_draft,
    delete_message,
    list_labels,
    list_messages,
    manifest,
    mark_as_read,
    mark_as_unread,
    read_message,
    remove_label,
    search_messages,
    send_message,
    unarchive_message,
)
from modulex_integrations.tools.gmail.outputs import (
    AddLabelOutput,
    ArchiveMessageOutput,
    CreateDraftOutput,
    DeleteMessageOutput,
    ListLabelsOutput,
    ListMessagesOutput,
    MarkAsReadOutput,
    MarkAsUnreadOutput,
    ReadMessageOutput,
    RemoveLabelOutput,
    SearchMessagesOutput,
    SendMessageOutput,
    UnarchiveMessageOutput,
)

API = "https://www.googleapis.com/gmail/v1"

_OAUTH_AUTH: dict[str, Any] = {
    "auth_type": "oauth2",
    "auth_data": {"access_token": "gmail-oauth-token"},
}
_PAT_AUTH: dict[str, Any] = {
    "auth_type": "bearer_token",
    "auth_data": {"token": "gmail-pat-token"},
}


def _args(auth: dict[str, Any], **extra: Any) -> dict[str, Any]:
    return dict(auth, **extra)


def _b64url(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode("utf-8")).decode("utf-8")


class TestManifest:
    def test_manifest_exposes_thirteen_actions(self) -> None:
        assert len(manifest.actions) == 13

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_oauth2_and_bearer_token_auth(self) -> None:
        types = {a.auth_type for a in manifest.auth_schemas}
        assert types == {"oauth2", "bearer_token"}

    def test_oauth_config_carries_four_gmail_scopes(self) -> None:
        oauth = next(a for a in manifest.auth_schemas if a.auth_type == "oauth2")
        assert len(oauth.oauth_config.scopes) == 4
        assert "https://www.googleapis.com/auth/gmail.send" in oauth.oauth_config.scopes


@pytest.mark.asyncio
async def test_send_message_oauth(httpx_mock: Any) -> None:
    captured: dict[str, Any] = {}

    def _capture(request: Any) -> Any:
        import json
        captured.update(json.loads(request.content.decode()))
        from httpx import Response
        return Response(
            200,
            json={"id": "M1", "threadId": "T1", "labelIds": ["SENT"]},
        )

    httpx_mock.add_callback(
        _capture, method="POST", url=f"{API}/users/me/messages/send"
    )
    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            _args(_OAUTH_AUTH, to="x@y.io", subject="Hi", body="Hello")
        )
    )
    assert result.success is True
    assert result.id == "M1"
    # The raw field is base64url-encoded MIME bytes that include "Hello".
    decoded = base64.urlsafe_b64decode(captured["raw"]).decode("utf-8")
    assert "Hello" in decoded
    assert "to: x@y.io" in decoded
    assert "subject: Hi" in decoded


@pytest.mark.asyncio
async def test_send_message_bearer(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/send",
        json={"id": "M1", "threadId": "T1", "labelIds": ["SENT"]},
    )
    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            _args(_PAT_AUTH, to="x@y.io", subject="Hi", body="Hi")
        )
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_send_message_validates_missing_token() -> None:
    bad = {"auth_type": "oauth2", "auth_data": {}}
    result = SendMessageOutput.model_validate(
        await send_message.ainvoke(
            dict(bad, to="x@y.io", subject="Hi", body="Hi")
        )
    )
    assert result.success is False
    assert result.error is not None and "access token" in result.error


@pytest.mark.asyncio
async def test_read_message_parses_payload(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/messages/M1?format=full",
        json={
            "id": "M1",
            "threadId": "T1",
            "labelIds": ["INBOX"],
            "snippet": "Hello",
            "internalDate": "1700000000000",
            "sizeEstimate": 100,
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Greetings"},
                    {"name": "From", "value": "a@x.io"},
                    {"name": "To", "value": "me@x.io"},
                    {"name": "Date", "value": "Fri, 16 May 2026 00:00:00 +0000"},
                ],
                "body": {"data": _b64url("Hello, world.")},
            },
        },
    )
    result = ReadMessageOutput.model_validate(
        await read_message.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert result.success is True
    assert result.subject == "Greetings"
    assert result.body == "Hello, world."


@pytest.mark.asyncio
async def test_read_message_multipart(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/messages/M1?format=full",
        json={
            "id": "M1",
            "threadId": "T1",
            "payload": {
                "headers": [{"name": "Subject", "value": "Multipart test"}],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": _b64url("plain text version")},
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": _b64url("<p>html version</p>")},
                    },
                ],
            },
        },
    )
    result = ReadMessageOutput.model_validate(
        await read_message.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert result.success is True
    # Plain-text preferred when both are present.
    assert result.body == "plain text version"


@pytest.mark.asyncio
async def test_search_messages_fetches_metadata_per_id(httpx_mock: Any) -> None:
    # First call: list IDs.
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/messages?q=is:unread&maxResults=10",
        json={
            "messages": [
                {"id": "M1", "threadId": "T1"},
                {"id": "M2", "threadId": "T2"},
            ],
            "resultSizeEstimate": 2,
        },
    )
    # Two follow-up calls for metadata. pytest_httpx is tolerant of
    # repeated identical query-string keys; we register a single
    # callback by URL pattern instead.
    import re

    def _metadata(request: Any) -> Any:
        from httpx import Response
        msg_id = str(request.url).rsplit("/", 1)[-1].split("?", 1)[0]
        return Response(
            200,
            json={
                "id": msg_id,
                "threadId": f"T{msg_id[-1]}",
                "snippet": f"snip {msg_id}",
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": f"sub {msg_id}"},
                        {"name": "From", "value": "x@y.io"},
                        {"name": "Date", "value": "today"},
                    ]
                },
            },
        )

    httpx_mock.add_callback(
        _metadata,
        method="GET",
        url=re.compile(rf"{API}/users/me/messages/M\d.*"),
        is_reusable=True,
    )
    result = SearchMessagesOutput.model_validate(
        await search_messages.ainvoke(_args(_OAUTH_AUTH, query="is:unread"))
    )
    assert result.success is True
    assert result.total == 2
    assert {m.id for m in result.messages} == {"M1", "M2"}


@pytest.mark.asyncio
async def test_list_messages(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/messages?labelIds=INBOX&maxResults=20&includeSpamTrash=false",
        json={"messages": [{"id": "M1", "threadId": "T1"}]},
    )
    httpx_mock.add_response(
        method="GET",
        url=(
            f"{API}/users/me/messages/M1"
            "?format=metadata&metadataHeaders=Subject&metadataHeaders=From&metadataHeaders=Date"
        ),
        json={
            "id": "M1",
            "threadId": "T1",
            "snippet": "Hi",
            "labelIds": ["INBOX"],
            "payload": {"headers": [{"name": "Subject", "value": "Hi"}]},
        },
    )
    result = ListMessagesOutput.model_validate(
        await list_messages.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True
    assert result.total == 1
    assert result.messages[0].subject == "Hi"


@pytest.mark.asyncio
async def test_create_draft(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/drafts",
        status_code=201,
        json={"id": "D1", "message": {"id": "M1", "threadId": "T1"}},
    )
    result = CreateDraftOutput.model_validate(
        await create_draft.ainvoke(
            _args(_OAUTH_AUTH, to="x@y.io", subject="Draft", body="hi")
        )
    )
    assert result.success is True
    assert result.draft_id == "D1"


@pytest.mark.asyncio
async def test_mark_as_read(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/modify",
        json={"id": "M1", "threadId": "T1", "labelIds": ["INBOX"]},
    )
    result = MarkAsReadOutput.model_validate(
        await mark_as_read.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert result.success is True
    assert "UNREAD" not in result.label_ids


@pytest.mark.asyncio
async def test_mark_as_unread(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/modify",
        json={"id": "M1", "threadId": "T1", "labelIds": ["INBOX", "UNREAD"]},
    )
    result = MarkAsUnreadOutput.model_validate(
        await mark_as_unread.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_archive_and_unarchive(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/modify",
        json={"id": "M1", "threadId": "T1", "labelIds": []},
    )
    arch = ArchiveMessageOutput.model_validate(
        await archive_message.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert arch.success is True

    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/modify",
        json={"id": "M1", "threadId": "T1", "labelIds": ["INBOX"]},
    )
    unarch = UnarchiveMessageOutput.model_validate(
        await unarchive_message.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert unarch.success is True
    assert "INBOX" in unarch.label_ids


@pytest.mark.asyncio
async def test_delete_message(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/trash",
        json={"id": "M1", "threadId": "T1"},
    )
    result = DeleteMessageOutput.model_validate(
        await delete_message.ainvoke(_args(_OAUTH_AUTH, message_id="M1"))
    )
    assert result.success is True


@pytest.mark.asyncio
async def test_add_label_and_remove_label(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/modify",
        json={"id": "M1", "threadId": "T1", "labelIds": ["INBOX", "STARRED"]},
    )
    add = AddLabelOutput.model_validate(
        await add_label.ainvoke(
            _args(_OAUTH_AUTH, message_id="M1", label_ids=["STARRED"])
        )
    )
    assert add.success is True
    assert add.added_labels == ["STARRED"]

    httpx_mock.add_response(
        method="POST",
        url=f"{API}/users/me/messages/M1/modify",
        json={"id": "M1", "threadId": "T1", "labelIds": ["INBOX"]},
    )
    rem = RemoveLabelOutput.model_validate(
        await remove_label.ainvoke(
            _args(_OAUTH_AUTH, message_id="M1", label_ids=["STARRED"])
        )
    )
    assert rem.success is True
    assert rem.removed_labels == ["STARRED"]


@pytest.mark.asyncio
async def test_list_labels(httpx_mock: Any) -> None:
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/users/me/labels",
        json={
            "labels": [
                {"id": "INBOX", "name": "INBOX", "type": "system"},
                {"id": "L1", "name": "My Label", "type": "user"},
            ]
        },
    )
    result = ListLabelsOutput.model_validate(
        await list_labels.ainvoke(_args(_OAUTH_AUTH))
    )
    assert result.success is True
    assert result.total == 2
