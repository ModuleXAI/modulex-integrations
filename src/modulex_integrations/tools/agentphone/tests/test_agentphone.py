"""Tests for the AgentPhone integration.

One happy-path test per action (22), plus failure-path tests for the
non-2xx -> success=False branch (including the API's ``detail``
unwrapping) and an empty-credential test (the API key guard
short-circuits before any HTTP call).
"""
from __future__ import annotations

import json
from typing import Any

import pytest

from modulex_integrations.tools.agentphone import (
    TOOLS,
    create_call,
    create_contact,
    create_number,
    delete_contact,
    get_call,
    get_call_transcript,
    get_contact,
    get_conversation,
    get_conversation_messages,
    get_number_messages,
    get_usage,
    get_usage_daily,
    get_usage_monthly,
    list_calls,
    list_contacts,
    list_conversations,
    list_numbers,
    manifest,
    react_to_message,
    release_number,
    send_message,
    update_contact,
    update_conversation,
)
from modulex_integrations.tools.agentphone.outputs import (
    CreateCallOutput,
    CreateContactOutput,
    CreateNumberOutput,
    DeleteContactOutput,
    GetCallOutput,
    GetCallTranscriptOutput,
    GetContactOutput,
    GetConversationMessagesOutput,
    GetConversationOutput,
    GetNumberMessagesOutput,
    GetUsageDailyOutput,
    GetUsageMonthlyOutput,
    GetUsageOutput,
    ListCallsOutput,
    ListContactsOutput,
    ListConversationsOutput,
    ListNumbersOutput,
    ReactToMessageOutput,
    ReleaseNumberOutput,
    SendMessageOutput,
    UpdateContactOutput,
    UpdateConversationOutput,
)

API = "https://api.agentphone.ai/v1"
_API_KEY = "fake-api-key"

_NUMBER = {
    "id": "num_1",
    "phoneNumber": "+14155551234",
    "country": "US",
    "status": "active",
    "type": "sms",
    "agentId": "agt_1",
    "createdAt": "2026-01-01T00:00:00Z",
}

_CALL = {
    "id": "call_1",
    "agentId": "agt_1",
    "phoneNumberId": "num_1",
    "phoneNumber": "+14155551234",
    "fromNumber": "+14155551234",
    "toNumber": "+14155559876",
    "direction": "outbound",
    "status": "completed",
    "startedAt": "2026-01-01T00:00:00Z",
    "endedAt": "2026-01-01T00:02:00Z",
    "durationSeconds": 120,
    "lastTranscriptSnippet": "Thanks, goodbye.",
    "recordingUrl": "https://cdn.agentphone.ai/recordings/call_1.mp3",
    "recordingAvailable": True,
}

_CONVERSATION_MESSAGE = {
    "id": "msg_1",
    "body": "Hello there",
    "fromNumber": "+14155551234",
    "toNumber": "+14155559876",
    "direction": "outbound",
    "channel": "imessage",
    "mediaUrl": None,
    "mediaUrls": ["https://cdn.example.com/a.png"],
    "receivedAt": "2026-01-01T00:00:00Z",
}

_CONTACT = {
    "id": "contact_1",
    "phoneNumber": "+14155559876",
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "notes": "VIP",
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-01-02T00:00:00Z",
}


def _args(**extra: Any) -> dict[str, Any]:
    return dict(api_key=_API_KEY, **extra)


# --- Manifest sanity --------------------------------------------------------


class TestManifest:
    def test_manifest_exposes_22_actions(self) -> None:
        assert len(manifest.actions) == 22

    def test_manifest_actions_match_tools_tuple(self) -> None:
        assert {a.name for a in manifest.actions} == {t.name for t in TOOLS}

    def test_manifest_has_api_key_auth(self) -> None:
        assert {a.auth_type for a in manifest.auth_schemas} == {"api_key"}

    def test_manifest_logo(self) -> None:
        assert manifest.logo == "modulex:agentphone-themed"


# --- Phone number actions ---------------------------------------------------


@pytest.mark.asyncio
async def test_create_number(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/numbers", json=_NUMBER)

    result_dict = await create_number.ainvoke(_args(country="US", area_code="415"))
    assert isinstance(result_dict, dict)
    result = CreateNumberOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "num_1"
    assert result.phone_number == "+14155551234"
    assert result.type == "sms"

    sent = httpx_mock.get_requests()[0]
    assert sent.headers["Authorization"] == f"Bearer {_API_KEY}"


@pytest.mark.asyncio
async def test_list_numbers(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/numbers?limit=2&offset=0",
        json={"data": [_NUMBER], "hasMore": False, "total": 1},
    )

    result_dict = await list_numbers.ainvoke(_args(limit=2, offset=0))
    result = ListNumbersOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.has_more is False
    assert result.data[0].agent_id == "agt_1"


@pytest.mark.asyncio
async def test_release_number(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/numbers/num_1", json={})

    result_dict = await release_number.ainvoke(_args(number_id="num_1"))
    result = ReleaseNumberOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "num_1"
    assert result.released is True


@pytest.mark.asyncio
async def test_get_number_messages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/numbers/num_1/messages?limit=1",
        json={
            "data": [
                {
                    "id": "msg_9",
                    "from_": "+14155559876",
                    "to": "+14155551234",
                    "body": "Hi!",
                    "direction": "inbound",
                    "channel": "sms",
                    "receivedAt": "2026-01-01T00:00:00Z",
                }
            ],
            "hasMore": True,
        },
    )

    result_dict = await get_number_messages.ainvoke(_args(number_id="num_1", limit=1))
    result = GetNumberMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.has_more is True
    assert result.data[0].from_ == "+14155559876"
    assert result.data[0].to == "+14155551234"


# --- Call actions -----------------------------------------------------------


@pytest.mark.asyncio
async def test_create_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/calls",
        json={
            "id": "call_1",
            "agentId": "agt_1",
            "status": "queued",
            "toNumber": "+14155559876",
            "fromNumber": "+14155551234",
            "phoneNumberId": "num_1",
            "direction": "outbound",
            "startedAt": "2026-01-01T00:00:00Z",
        },
    )

    result_dict = await create_call.ainvoke(
        _args(
            agent_id="agt_1",
            to_number="+14155559876",
            initial_greeting="Hi, this is Acme.",
            system_prompt="You are a friendly agent.",
        )
    )
    result = CreateCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "call_1"
    assert result.status == "queued"
    assert result.direction == "outbound"


@pytest.mark.asyncio
async def test_list_calls(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calls?status=completed&direction=outbound",
        json={"data": [_CALL], "hasMore": False, "total": 1},
    )

    result_dict = await list_calls.ainvoke(_args(status="completed", direction="outbound"))
    result = ListCallsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.data[0].duration_seconds == 120
    assert result.data[0].recording_available is True


@pytest.mark.asyncio
async def test_get_call(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calls/call_1",
        json={
            **_CALL,
            "transcripts": [
                {
                    "id": "t_1",
                    "transcript": "Hello?",
                    "confidence": 0.94,
                    "response": "Hi, this is Acme.",
                    "createdAt": "2026-01-01T00:00:05Z",
                }
            ],
        },
    )

    result_dict = await get_call.ainvoke(_args(call_id="call_1"))
    result = GetCallOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "call_1"
    assert result.recording_url == "https://cdn.agentphone.ai/recordings/call_1.mp3"
    assert result.transcripts[0].confidence == 0.94
    assert result.transcripts[0].response == "Hi, this is Acme."


@pytest.mark.asyncio
async def test_get_call_transcript(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/calls/call_1/transcript",
        json={
            "callId": "call_1",
            "transcript": [
                {"role": "user", "content": "Hello?", "createdAt": "2026-01-01T00:00:05Z"},
                {"role": "agent", "content": "Hi!", "created_at": "2026-01-01T00:00:07Z"},
            ],
        },
    )

    result_dict = await get_call_transcript.ainvoke(_args(call_id="call_1"))
    result = GetCallTranscriptOutput.model_validate(result_dict)
    assert result.success is True
    assert result.call_id == "call_1"
    assert [turn.role for turn in result.transcript] == ["user", "agent"]
    assert result.transcript[1].created_at == "2026-01-01T00:00:07Z"


# --- Conversation actions ---------------------------------------------------


@pytest.mark.asyncio
async def test_list_conversations(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations?limit=1",
        json={
            "data": [
                {
                    "id": "conv_1",
                    "agentId": "agt_1",
                    "phoneNumberId": "num_1",
                    "phoneNumber": "+14155551234",
                    "participant": "+14155559876",
                    "lastMessageAt": "2026-01-01T00:00:00Z",
                    "lastMessagePreview": "Hello there",
                    "messageCount": 4,
                    "metadata": {"orderId": "ORD-1"},
                    "createdAt": "2026-01-01T00:00:00Z",
                }
            ],
            "hasMore": False,
            "total": 1,
        },
    )

    result_dict = await list_conversations.ainvoke(_args(limit=1))
    result = ListConversationsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.data[0].message_count == 4
    assert result.data[0].metadata == {"orderId": "ORD-1"}
    assert result.data[0].last_message_preview == "Hello there"


@pytest.mark.asyncio
async def test_get_conversation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations/conv_1?message_limit=10",
        json={
            "id": "conv_1",
            "agentId": "agt_1",
            "phoneNumberId": "num_1",
            "phoneNumber": "+14155551234",
            "participant": "+14155559876",
            "lastMessageAt": "2026-01-01T00:00:00Z",
            "messageCount": 1,
            "metadata": None,
            "createdAt": "2026-01-01T00:00:00Z",
            "messages": [_CONVERSATION_MESSAGE],
        },
    )

    result_dict = await get_conversation.ainvoke(
        _args(conversation_id="conv_1", message_limit=10)
    )
    result = GetConversationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.participant == "+14155559876"
    assert result.messages[0].media_urls == ["https://cdn.example.com/a.png"]


@pytest.mark.asyncio
async def test_update_conversation(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/conversations/conv_1",
        json={
            "id": "conv_1",
            "agentId": "agt_1",
            "phoneNumberId": "num_1",
            "phoneNumber": "+14155551234",
            "participant": "+14155559876",
            "lastMessageAt": "2026-01-01T00:00:00Z",
            "messageCount": 1,
            "metadata": {"customerName": "Jane"},
            "createdAt": "2026-01-01T00:00:00Z",
            "messages": [],
        },
    )

    result_dict = await update_conversation.ainvoke(
        _args(conversation_id="conv_1", metadata={"customerName": "Jane"})
    )
    result = UpdateConversationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata == {"customerName": "Jane"}

    sent = httpx_mock.get_requests()[0]
    assert b'"customerName"' in sent.content


@pytest.mark.asyncio
async def test_update_conversation_clears_metadata(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/conversations/conv_1",
        json={"id": "conv_1", "metadata": None, "messages": []},
    )

    result_dict = await update_conversation.ainvoke(
        _args(conversation_id="conv_1", clear_metadata=True)
    )
    result = UpdateConversationOutput.model_validate(result_dict)
    assert result.success is True
    assert result.metadata is None

    sent = httpx_mock.get_requests()[0]
    assert sent.content == b'{"metadata":null}'


@pytest.mark.asyncio
async def test_get_conversation_messages(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/conversations/conv_1/messages?limit=1&after=2026-01-01T00%3A00%3A00Z",
        json={"data": [_CONVERSATION_MESSAGE], "hasMore": False},
    )

    result_dict = await get_conversation_messages.ainvoke(
        _args(conversation_id="conv_1", limit=1, after="2026-01-01T00:00:00Z")
    )
    result = GetConversationMessagesOutput.model_validate(result_dict)
    assert result.success is True
    assert result.has_more is False
    assert result.data[0].channel == "imessage"


# --- Message actions --------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/messages",
        json={
            "id": "msg_1",
            "status": "queued",
            "channel": "imessage",
            "from_number": "+14155551234",
            "to_number": "+14155559876",
        },
    )

    result_dict = await send_message.ainvoke(
        _args(agent_id="agt_1", to_number="+14155559876", body="Hi!")
    )
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "msg_1"
    assert result.from_number == "+14155551234"
    assert result.channel == "imessage"

    sent = httpx_mock.get_requests()[0]
    assert b'"to_number"' in sent.content


@pytest.mark.asyncio
async def test_send_message_supports_media_urls(httpx_mock):  # type: ignore[no-untyped-def]
    """The vendor deprecated singular `media_url` in favour of `media_urls`."""
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/messages",
        json={"id": "msg_2", "status": "queued", "channel": "imessage"},
    )

    result_dict = await send_message.ainvoke(
        _args(
            agent_id="agt_1",
            to_number="+14155559876",
            body="",
            media_urls=["https://example.com/a.png", "https://example.com/b.png"],
        )
    )
    assert SendMessageOutput.model_validate(result_dict).success is True

    body = json.loads(httpx_mock.get_requests()[0].content)
    assert body["media_urls"] == [
        "https://example.com/a.png",
        "https://example.com/b.png",
    ]
    # The deprecated singular field is not emitted when it was not supplied.
    assert "media_url" not in body


@pytest.mark.asyncio
async def test_react_to_message(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/messages/msg_1/reactions",
        json={
            "id": "rct_1",
            "reaction_type": "love",
            "message_id": "msg_1",
            "channel": "imessage",
        },
    )

    result_dict = await react_to_message.ainvoke(_args(message_id="msg_1", reaction="love"))
    result = ReactToMessageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.reaction_type == "love"
    assert result.message_id == "msg_1"


# --- Contact actions --------------------------------------------------------


@pytest.mark.asyncio
async def test_create_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="POST", url=f"{API}/contacts", json=_CONTACT)

    result_dict = await create_contact.ainvoke(
        _args(phone_number="+14155559876", name="Alice Johnson", email="alice@example.com")
    )
    result = CreateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact_1"
    assert result.email == "alice@example.com"


@pytest.mark.asyncio
async def test_list_contacts(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts?search=Alice",
        json={"data": [_CONTACT], "hasMore": False, "total": 1},
    )

    result_dict = await list_contacts.ainvoke(_args(search="Alice"))
    result = ListContactsOutput.model_validate(result_dict)
    assert result.success is True
    assert result.total == 1
    assert result.data[0].name == "Alice Johnson"


@pytest.mark.asyncio
async def test_get_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="GET", url=f"{API}/contacts/contact_1", json=_CONTACT)

    result_dict = await get_contact.ainvoke(_args(contact_id="contact_1"))
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.phone_number == "+14155559876"
    assert result.notes == "VIP"


@pytest.mark.asyncio
async def test_update_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="PATCH",
        url=f"{API}/contacts/contact_1",
        json={**_CONTACT, "name": "Alice J."},
    )

    result_dict = await update_contact.ainvoke(_args(contact_id="contact_1", name="Alice J."))
    result = UpdateContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.name == "Alice J."
    assert result.updated_at == "2026-01-02T00:00:00Z"


@pytest.mark.asyncio
async def test_delete_contact(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(method="DELETE", url=f"{API}/contacts/contact_1", json={})

    result_dict = await delete_contact.ainvoke(_args(contact_id="contact_1"))
    result = DeleteContactOutput.model_validate(result_dict)
    assert result.success is True
    assert result.id == "contact_1"
    assert result.deleted is True


# --- Usage actions ----------------------------------------------------------


@pytest.mark.asyncio
async def test_get_usage(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/usage",
        json={
            "plan": {
                "name": "growth",
                "limits": {
                    "numbers": 10,
                    "messagesPerMonth": 5000,
                    "voiceMinutesPerMonth": 1000,
                    "maxCallDurationMinutes": 30,
                    "concurrentCalls": 5,
                },
            },
            "numbers": {"used": 3, "limit": 10, "remaining": 7},
            "stats": {
                "totalMessages": 120,
                "messagesLast24h": 4,
                "messagesLast7d": 30,
                "messagesLast30d": 110,
                "totalCalls": 12,
                "callsLast24h": 1,
                "callsLast7d": 5,
                "callsLast30d": 11,
                "totalWebhookDeliveries": 200,
                "successfulWebhookDeliveries": 198,
                "failedWebhookDeliveries": 2,
            },
            "periodStart": "2026-01-01T00:00:00Z",
            "periodEnd": "2026-02-01T00:00:00Z",
        },
    )

    result_dict = await get_usage.ainvoke(_args())
    result = GetUsageOutput.model_validate(result_dict)
    assert result.success is True
    assert result.plan is not None
    assert result.plan.name == "growth"
    assert result.plan.limits is not None
    assert result.plan.limits.messages_per_month == 5000
    assert result.numbers is not None
    assert result.numbers.remaining == 7
    assert result.stats is not None
    assert result.stats.failed_webhook_deliveries == 2
    assert result.period_end == "2026-02-01T00:00:00Z"


@pytest.mark.asyncio
async def test_get_usage_daily(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/usage/daily?days=2",
        json={
            "data": [
                {"date": "2026-01-01", "messages": 3, "calls": 1, "webhooks": 4},
                {"date": "2026-01-02", "messages": 5, "calls": 0, "webhooks": 5},
            ],
            "days": 2,
        },
    )

    result_dict = await get_usage_daily.ainvoke(_args(days=2))
    result = GetUsageDailyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.days == 2
    assert result.data[1].messages == 5


@pytest.mark.asyncio
async def test_get_usage_monthly(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/usage/monthly?months=1",
        json={
            "data": [{"month": "2026-01", "messages": 110, "calls": 11, "webhooks": 200}],
            "months": 1,
        },
    )

    result_dict = await get_usage_monthly.ainvoke(_args(months=1))
    result = GetUsageMonthlyOutput.model_validate(result_dict)
    assert result.success is True
    assert result.months == 1
    assert result.data[0].month == "2026-01"


# --- Failure paths ----------------------------------------------------------


@pytest.mark.asyncio
async def test_non_2xx_unwraps_detail_string(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="GET",
        url=f"{API}/contacts/missing",
        status_code=404,
        json={"detail": "Contact not found"},
    )

    result_dict = await get_contact.ainvoke(_args(contact_id="missing"))
    result = GetContactOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "404" in result.error
    assert "Contact not found" in result.error
    assert result.id is None


@pytest.mark.asyncio
async def test_non_2xx_unwraps_validation_detail_list(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="POST",
        url=f"{API}/messages",
        status_code=422,
        json={"detail": [{"loc": ["body", "body"], "msg": "field required"}]},
    )

    result_dict = await send_message.ainvoke(
        _args(agent_id="agt_1", to_number="+14155559876", body="")
    )
    result = SendMessageOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "field required" in result.error


@pytest.mark.asyncio
async def test_release_number_failure_keeps_id(httpx_mock):  # type: ignore[no-untyped-def]
    httpx_mock.add_response(
        method="DELETE",
        url=f"{API}/numbers/num_missing",
        status_code=404,
        json={"message": "Number not found"},
    )

    result_dict = await release_number.ainvoke(_args(number_id="num_missing"))
    result = ReleaseNumberOutput.model_validate(result_dict)
    assert result.success is False
    assert result.released is False
    assert result.id == "num_missing"
    assert result.error is not None
    assert "Number not found" in result.error


# --- Empty-credential guard -------------------------------------------------


@pytest.mark.asyncio
async def test_empty_api_key_short_circuits(httpx_mock):  # type: ignore[no-untyped-def]
    result_dict = await list_numbers.ainvoke({"api_key": "   "})
    result = ListNumbersOutput.model_validate(result_dict)
    assert result.success is False
    assert result.error is not None
    assert "API key is empty" in result.error
    assert httpx_mock.get_requests() == []
