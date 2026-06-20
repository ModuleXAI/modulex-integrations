"""Tests for the AgentMail integration.

One happy-path test per action (21), plus a failure-path test for the
non-2xx -> success=False branch and an empty-credential test (the API
key guard short-circuits before any HTTP call).
"""
from __future__ import annotations

from typing import Any

import pytest

from modulex_integrations.tools.agentmail import (
    TOOLS,
    create_draft,
    create_inbox,
    delete_draft,
    delete_inbox,
    delete_thread,
    forward_message,
    get_draft,
    get_inbox,
    get_message,
    get_thread,
    list_drafts,
    list_inboxes,
    list_messages,
    list_threads,
    manifest,
    reply_message,
    send_draft,
    send_message,
    update_draft,
    update_inbox,
    update_message,
    update_thread,
)
from modulex_integrations.tools.agentmail.outputs import (
    CreateDraftOutput,
    CreateInboxOutput,
    DeleteDraftOutput,
    DeleteInboxOutput,
    DeleteThreadOutput,
    ForwardMessageOutput,
    GetDraftOutput,
    GetInboxOutput,
    GetMessageOutput,
    GetThreadOutput,
    ListDraftsOutput,
    ListInboxesOutput,
    ListMessagesOutput,
    ListThreadsOutput,
    ReplyMessageOutput,
    SendDraftOutput,
    SendMessageOutput,
    UpdateDraftOutput,
    UpdateInboxOutput,
    UpdateMessageOutput,
    UpdateThreadOutput,
)

API = "https://api.agentmail.to/v0"
_API_KEY = "fake-api-key"
_INBOX = "inbox_123"


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_21_actions(self) -> None:
        assert len(manifest.actions) == 21

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:agentmail-themed"


# --- Inbox actions ---------------------------------------------------------


@pytest.mark.asyncio
async def test_create_inbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes",
        json={
            "inbox_id": "inbox_1",
            "email": "agent@agentmail.to",
            "display_name": "Agent",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        },
    )

    result_dict = await create_inbox.ainvoke(_args(display_name="Agent"))
    assert isinstance(result_dict, dict)
    result = CreateInboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.inbox_id == "inbox_1"
    assert result.email == "agent@agentmail.to"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_list_inboxes(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes?limit=5",
        json={
            "inboxes": [
                {"inbox_id": "inbox_1", "email": "a@agentmail.to", "display_name": None}
            ],
            "count": 1,
            "next_page_token": None,
        },
    )

    result_dict = await list_inboxes.ainvoke(_args(limit=5))
    result = ListInboxesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.inboxes[0].inbox_id == "inbox_1"
    assert result.count == 1


@pytest.mark.asyncio
async def test_get_inbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}",
        json={"inbox_id": _INBOX, "email": "a@agentmail.to", "display_name": "A"},
    )

    result_dict = await get_inbox.ainvoke(_args(inbox_id=_INBOX))
    result = GetInboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.inbox_id == _INBOX


@pytest.mark.asyncio
async def test_update_inbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/inboxes/{_INBOX}",
        json={"inbox_id": _INBOX, "email": "a@agentmail.to", "display_name": "New"},
    )

    result_dict = await update_inbox.ainvoke(_args(inbox_id=_INBOX, display_name="New"))
    result = UpdateInboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.display_name == "New"


@pytest.mark.asyncio
async def test_delete_inbox(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/inboxes/{_INBOX}", status_code=204)

    result_dict = await delete_inbox.ainvoke(_args(inbox_id=_INBOX))
    result = DeleteInboxOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


# --- Message actions -------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/messages/send",
        json={"message_id": "msg_1", "thread_id": "thr_1"},
    )

    result_dict = await send_message.ainvoke(
        _args(inbox_id=_INBOX, to="bob@example.com", subject="Hi", text="Hello")
    )
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg_1"
    assert result.thread_id == "thr_1"
    assert result.subject == "Hi"
    assert result.to == "bob@example.com"


@pytest.mark.asyncio
async def test_reply_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/messages/msg_1/reply",
        json={"message_id": "msg_2", "thread_id": "thr_1"},
    )

    result_dict = await reply_message.ainvoke(
        _args(inbox_id=_INBOX, message_id="msg_1", text="Thanks")
    )
    result = ReplyMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg_2"


@pytest.mark.asyncio
async def test_reply_message_reply_all(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/messages/msg_1/reply-all",
        json={"message_id": "msg_3", "thread_id": "thr_1"},
    )

    result_dict = await reply_message.ainvoke(
        _args(inbox_id=_INBOX, message_id="msg_1", text="Thanks", reply_all=True)
    )
    result = ReplyMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg_3"


@pytest.mark.asyncio
async def test_forward_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/messages/msg_1/forward",
        json={"message_id": "msg_4", "thread_id": "thr_2"},
    )

    result_dict = await forward_message.ainvoke(
        _args(inbox_id=_INBOX, message_id="msg_1", to="carol@example.com")
    )
    result = ForwardMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.thread_id == "thr_2"


@pytest.mark.asyncio
async def test_list_messages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}/messages",
        json={
            "messages": [
                {
                    "message_id": "msg_1",
                    "from": "a@example.com",
                    "to": ["b@example.com"],
                    "subject": "Hi",
                    "preview": "Hello there",
                }
            ],
            "count": 1,
            "next_page_token": None,
        },
    )

    result_dict = await list_messages.ainvoke(_args(inbox_id=_INBOX))
    result = ListMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.messages[0].message_id == "msg_1"
    assert result.messages[0].from_ == "a@example.com"


@pytest.mark.asyncio
async def test_get_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}/messages/msg_1",
        json={
            "message_id": "msg_1",
            "thread_id": "thr_1",
            "from": "a@example.com",
            "to": ["b@example.com"],
            "subject": "Hi",
            "text": "Hello",
            "labels": ["inbox"],
        },
    )

    result_dict = await get_message.ainvoke(_args(inbox_id=_INBOX, message_id="msg_1"))
    result = GetMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.from_ == "a@example.com"
    assert result.labels == ["inbox"]


@pytest.mark.asyncio
async def test_update_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/inboxes/{_INBOX}/messages/msg_1",
        json={"message_id": "msg_1", "labels": ["important"]},
    )

    result_dict = await update_message.ainvoke(
        _args(inbox_id=_INBOX, message_id="msg_1", add_labels="important")
    )
    result = UpdateMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.labels == ["important"]


# --- Thread actions --------------------------------------------------------


@pytest.mark.asyncio
async def test_list_threads(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}/threads",
        json={
            "threads": [
                {
                    "thread_id": "thr_1",
                    "subject": "Hi",
                    "senders": ["a@example.com"],
                    "recipients": ["b@example.com"],
                    "message_count": 2,
                    "timestamp": "2026-01-02T00:00:00Z",
                }
            ],
            "count": 1,
            "next_page_token": None,
        },
    )

    result_dict = await list_threads.ainvoke(_args(inbox_id=_INBOX))
    result = ListThreadsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.threads[0].thread_id == "thr_1"
    assert result.threads[0].last_message_at == "2026-01-02T00:00:00Z"


@pytest.mark.asyncio
async def test_get_thread(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}/threads/thr_1",
        json={
            "thread_id": "thr_1",
            "subject": "Hi",
            "senders": ["a@example.com"],
            "recipients": ["b@example.com"],
            "message_count": 1,
            "labels": ["inbox"],
            "messages": [
                {
                    "message_id": "msg_1",
                    "from": "a@example.com",
                    "to": ["b@example.com"],
                    "subject": "Hi",
                    "text": "Hello",
                }
            ],
        },
    )

    result_dict = await get_thread.ainvoke(_args(inbox_id=_INBOX, thread_id="thr_1"))
    result = GetThreadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.messages[0].message_id == "msg_1"
    assert result.messages[0].from_ == "a@example.com"


@pytest.mark.asyncio
async def test_update_thread(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/inboxes/{_INBOX}/threads/thr_1",
        json={"thread_id": "thr_1", "labels": ["follow-up"]},
    )

    result_dict = await update_thread.ainvoke(
        _args(inbox_id=_INBOX, thread_id="thr_1", add_labels="follow-up")
    )
    result = UpdateThreadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.labels == ["follow-up"]


@pytest.mark.asyncio
async def test_delete_thread(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/inboxes/{_INBOX}/threads/thr_1", status_code=204
    )

    result_dict = await delete_thread.ainvoke(_args(inbox_id=_INBOX, thread_id="thr_1"))
    result = DeleteThreadOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


# --- Draft actions ---------------------------------------------------------


@pytest.mark.asyncio
async def test_create_draft(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/drafts",
        json={
            "draft_id": "drf_1",
            "inbox_id": _INBOX,
            "subject": "Draft",
            "to": ["b@example.com"],
            "labels": ["draft"],
        },
    )

    result_dict = await create_draft.ainvoke(
        _args(inbox_id=_INBOX, to="b@example.com", subject="Draft", text="Body")
    )
    result = CreateDraftOutput.model_validate(result_dict)
    assert result.success is True
    assert result.draft_id == "drf_1"
    assert result.to == ["b@example.com"]


@pytest.mark.asyncio
async def test_list_drafts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}/drafts",
        json={
            "drafts": [
                {
                    "draft_id": "drf_1",
                    "inbox_id": _INBOX,
                    "subject": "Draft",
                    "to": ["b@example.com"],
                }
            ],
            "count": 1,
            "next_page_token": None,
        },
    )

    result_dict = await list_drafts.ainvoke(_args(inbox_id=_INBOX))
    result = ListDraftsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.drafts[0].draft_id == "drf_1"


@pytest.mark.asyncio
async def test_get_draft(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/inboxes/{_INBOX}/drafts/drf_1",
        json={
            "draft_id": "drf_1",
            "inbox_id": _INBOX,
            "subject": "Draft",
            "to": ["b@example.com"],
            "text": "Body",
        },
    )

    result_dict = await get_draft.ainvoke(_args(inbox_id=_INBOX, draft_id="drf_1"))
    result = GetDraftOutput.model_validate(result_dict)
    assert result.success is True
    assert result.text == "Body"


@pytest.mark.asyncio
async def test_update_draft(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/inboxes/{_INBOX}/drafts/drf_1",
        json={
            "draft_id": "drf_1",
            "inbox_id": _INBOX,
            "subject": "Updated",
            "to": ["b@example.com"],
        },
    )

    result_dict = await update_draft.ainvoke(
        _args(inbox_id=_INBOX, draft_id="drf_1", subject="Updated")
    )
    result = UpdateDraftOutput.model_validate(result_dict)
    assert result.success is True
    assert result.subject == "Updated"


@pytest.mark.asyncio
async def test_delete_draft(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE", url=f"{API}/inboxes/{_INBOX}/drafts/drf_1", status_code=204
    )

    result_dict = await delete_draft.ainvoke(_args(inbox_id=_INBOX, draft_id="drf_1"))
    result = DeleteDraftOutput.model_validate(result_dict)
    assert result.success is True
    assert result.deleted is True


@pytest.mark.asyncio
async def test_send_draft(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/drafts/drf_1/send",
        json={"message_id": "msg_5", "thread_id": "thr_3"},
    )

    result_dict = await send_draft.ainvoke(_args(inbox_id=_INBOX, draft_id="drf_1"))
    result = SendDraftOutput.model_validate(result_dict)
    assert result.success is True
    assert result.message_id == "msg_5"


# --- Failure-path + empty-credential --------------------------------------


@pytest.mark.asyncio
async def test_send_message_non_2xx_sets_success_false(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/inboxes/{_INBOX}/messages/send",
        status_code=422,
        json={"message": "Invalid recipient"},
    )

    result_dict = await send_message.ainvoke(
        _args(inbox_id=_INBOX, to="bad", subject="Hi", text="Hello")
    )
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "422" in result.error


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits() -> None:
    result_dict = await list_inboxes.ainvoke({"api_key": "   "})
    result = ListInboxesOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "empty" in result.error.lower()
