"""AgentPhone LangChain ``@tool`` functions.

Twenty-two async tools wrapping the AgentPhone REST API
(``https://api.agentphone.ai/v1``). The calling convention is
*key-based*: the modulex ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's credential), not an
``auth_type``/``auth_data`` pair. The key is sent as
``Authorization: Bearer <api_key>``.

Error model: every call is guarded so non-2xx HTTP responses, timeouts,
and unexpected exceptions return the typed output with ``success=False``
+ ``error`` instead of raising. The API reports failures as
``{"detail": ...}`` (string or FastAPI-style validation list) or
``{"message": ...}``; both are unwrapped into the ``error`` string.
Successful payloads are parsed permissively with ``.get()``.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.agentphone.outputs import (
    CallSummary,
    Contact,
    ConversationMessage,
    ConversationSummary,
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
    NumberMessage,
    PhoneNumberSummary,
    ReactToMessageOutput,
    ReleaseNumberOutput,
    SendMessageOutput,
    TranscriptEntry,
    TranscriptTurn,
    UpdateContactOutput,
    UpdateConversationOutput,
    UsageDailyEntry,
    UsageMonthlyEntry,
    UsageNumbers,
    UsagePlan,
    UsagePlanLimits,
    UsageStats,
)

__all__ = [
    "create_call",
    "create_contact",
    "create_number",
    "delete_contact",
    "get_call",
    "get_call_transcript",
    "get_contact",
    "get_conversation",
    "get_conversation_messages",
    "get_number_messages",
    "get_usage",
    "get_usage_daily",
    "get_usage_monthly",
    "list_calls",
    "list_contacts",
    "list_conversations",
    "list_numbers",
    "react_to_message",
    "release_number",
    "send_message",
    "update_contact",
    "update_conversation",
]

_API_BASE = "https://api.agentphone.ai/v1"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = "AgentPhone API key is empty. Please configure a valid AgentPhone credential."


# --- Shared helpers --------------------------------------------------------


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _ok(response: httpx.Response) -> bool:
    return 200 <= response.status_code < 300


def _error(response: httpx.Response) -> str:
    """Unwrap the API's error payload into a single error string."""
    payload: Any = None
    try:
        payload = response.json()
    except Exception:
        payload = None

    detail: str | None = None
    if isinstance(payload, dict):
        raw = payload.get("detail")
        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, dict):
                msg = first.get("msg")
                if isinstance(msg, str) and msg:
                    detail = msg
        elif isinstance(raw, str) and raw:
            detail = raw
        if detail is None:
            message = payload.get("message")
            if isinstance(message, str) and message:
                detail = message

    return f"AgentPhone API error ({response.status_code}): {detail or response.text}"


def _as_dicts(value: Any) -> list[dict[str, Any]]:
    """Coerce a raw JSON value into a list of dict rows."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _as_dict(value: Any) -> dict[str, Any]:
    """Coerce a raw JSON value into a dict (empty when absent or null)."""
    if not isinstance(value, dict):
        return {}
    return value


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _phone_number(item: dict[str, Any]) -> PhoneNumberSummary:
    return PhoneNumberSummary(
        id=item.get("id"),
        phone_number=item.get("phoneNumber"),
        country=item.get("country"),
        status=item.get("status"),
        type=item.get("type"),
        agent_id=item.get("agentId"),
        created_at=item.get("createdAt"),
    )


def _number_message(item: dict[str, Any]) -> NumberMessage:
    return NumberMessage(
        id=item.get("id"),
        from_=item.get("from_"),
        to=item.get("to"),
        body=item.get("body"),
        direction=item.get("direction"),
        channel=item.get("channel"),
        received_at=item.get("receivedAt"),
    )


def _call_summary(item: dict[str, Any]) -> CallSummary:
    return CallSummary(
        id=item.get("id"),
        agent_id=item.get("agentId"),
        phone_number_id=item.get("phoneNumberId"),
        phone_number=item.get("phoneNumber"),
        from_number=item.get("fromNumber"),
        to_number=item.get("toNumber"),
        direction=item.get("direction"),
        status=item.get("status"),
        started_at=item.get("startedAt"),
        ended_at=item.get("endedAt"),
        duration_seconds=item.get("durationSeconds"),
        last_transcript_snippet=item.get("lastTranscriptSnippet"),
        recording_url=item.get("recordingUrl"),
        recording_available=item.get("recordingAvailable"),
    )


def _transcript_turn(item: dict[str, Any]) -> TranscriptTurn:
    return TranscriptTurn(
        id=item.get("id"),
        transcript=item.get("transcript"),
        confidence=item.get("confidence"),
        response=item.get("response"),
        created_at=item.get("createdAt"),
    )


def _transcript_entry(item: dict[str, Any]) -> TranscriptEntry:
    return TranscriptEntry(
        role=item.get("role"),
        content=item.get("content"),
        created_at=item.get("createdAt") or item.get("created_at"),
    )


def _conversation_summary(item: dict[str, Any]) -> ConversationSummary:
    return ConversationSummary(
        id=item.get("id"),
        agent_id=item.get("agentId"),
        phone_number_id=item.get("phoneNumberId"),
        phone_number=item.get("phoneNumber"),
        participant=item.get("participant"),
        last_message_at=item.get("lastMessageAt"),
        last_message_preview=item.get("lastMessagePreview"),
        message_count=item.get("messageCount"),
        metadata=item.get("metadata"),
        created_at=item.get("createdAt"),
    )


def _conversation_message(item: dict[str, Any]) -> ConversationMessage:
    return ConversationMessage(
        id=item.get("id"),
        body=item.get("body"),
        from_number=item.get("fromNumber"),
        to_number=item.get("toNumber"),
        direction=item.get("direction"),
        channel=item.get("channel"),
        media_url=item.get("mediaUrl"),
        media_urls=_as_str_list(item.get("mediaUrls")),
        received_at=item.get("receivedAt"),
    )


def _contact(item: dict[str, Any]) -> Contact:
    return Contact(
        id=item.get("id"),
        phone_number=item.get("phoneNumber"),
        name=item.get("name"),
        email=item.get("email"),
        notes=item.get("notes"),
        created_at=item.get("createdAt"),
        updated_at=item.get("updatedAt"),
    )


# --- Input schemas (args_schema for each @tool) ----------------------------


class CreateNumberInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    country: str | None = Field(
        default=None, description="Two-letter country code: 'US' or 'CA'. Defaults to US."
    )
    area_code: str | None = Field(
        default=None,
        description="Preferred area code (US/CA only, e.g. '415'). Best-effort.",
    )
    agent_id: str | None = Field(
        default=None, description="Optionally attach the number to this agent immediately"
    )


class ListNumbersInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Number of results to return (default 20, max 100)"
    )
    offset: int | None = Field(default=None, description="Number of results to skip (min 0)")


class ReleaseNumberInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    number_id: str = Field(description="ID of the phone number to release")


class GetNumberMessagesInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    number_id: str = Field(description="ID of the phone number")
    limit: int | None = Field(
        default=None, description="Number of messages to return (default 50, max 200)"
    )
    before: str | None = Field(
        default=None, description="Return messages received before this ISO 8601 timestamp"
    )
    after: str | None = Field(
        default=None, description="Return messages received after this ISO 8601 timestamp"
    )


class CreateCallInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    agent_id: str = Field(description="Agent that will handle the call")
    to_number: str = Field(
        description="Phone number to call in E.164 format (e.g. +14155551234)"
    )
    from_number_id: str | None = Field(
        default=None,
        description=(
            "Phone number ID to use as caller ID. Must belong to the agent. "
            "If omitted, the agent's first assigned number is used."
        ),
    )
    initial_greeting: str | None = Field(
        default=None, description="Greeting spoken when the recipient answers"
    )
    voice: str | None = Field(
        default=None,
        description="Voice ID override for this call (defaults to the agent's voice)",
    )
    system_prompt: str | None = Field(
        default=None,
        description=(
            "When provided, uses a built-in LLM for the conversation instead of "
            "forwarding to your webhook"
        ),
    )


class ListCallsInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Number of results to return (default 20, max 100)"
    )
    offset: int | None = Field(default=None, description="Number of results to skip (min 0)")
    status: str | None = Field(
        default=None, description="Filter by status: completed, in-progress, or failed"
    )
    direction: str | None = Field(
        default=None, description="Filter by direction: inbound or outbound"
    )
    type: str | None = Field(default=None, description="Filter by call type: pstn or web")
    search: str | None = Field(
        default=None, description="Search by phone number (matches fromNumber or toNumber)"
    )


class GetCallInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    call_id: str = Field(description="ID of the call to retrieve")


class GetCallTranscriptInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    call_id: str = Field(description="ID of the call to retrieve the transcript for")


class ListConversationsInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    limit: int | None = Field(
        default=None, description="Number of results to return (default 20, max 100)"
    )
    offset: int | None = Field(default=None, description="Number of results to skip (min 0)")


class GetConversationInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    conversation_id: str = Field(description="Conversation ID")
    message_limit: int | None = Field(
        default=None, description="Number of recent messages to include (default 50, max 100)"
    )


class UpdateConversationInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    conversation_id: str = Field(description="Conversation ID")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Custom key-value metadata to store on the conversation"
    )
    clear_metadata: bool = Field(
        default=False,
        description=(
            "Set to true to erase the conversation's stored metadata "
            "(takes precedence over 'metadata')"
        ),
    )


class GetConversationMessagesInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    conversation_id: str = Field(description="Conversation ID")
    limit: int | None = Field(
        default=None, description="Number of messages to return (default 50, max 200)"
    )
    before: str | None = Field(
        default=None, description="Return messages received before this ISO 8601 timestamp"
    )
    after: str | None = Field(
        default=None, description="Return messages received after this ISO 8601 timestamp"
    )


class SendMessageInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    agent_id: str = Field(description="Agent sending the message")
    to_number: str = Field(
        description="Recipient phone number in E.164 format (e.g. +14155551234)"
    )
    body: str = Field(description="Message text to send")
    media_url: str | None = Field(
        default=None,
        description=(
            "Deprecated by the vendor — prefer media_urls. URL of a single "
            "image, video, or file to attach"
        ),
    )
    media_urls: list[str] | None = Field(
        default=None,
        description="Public HTTPS URLs to attach (2-20 sends an iMessage carousel)",
    )
    number_id: str | None = Field(
        default=None,
        description=(
            "Phone number ID to send from. If omitted, the agent's first assigned "
            "number is used."
        ),
    )


class ReactToMessageInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    message_id: str = Field(description="ID of the message to react to")
    reaction: str = Field(
        description="Reaction type: love, like, dislike, laugh, emphasize, or question"
    )


class CreateContactInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    phone_number: str = Field(
        description="Phone number in E.164 format (e.g. +14155551234)"
    )
    name: str = Field(description="Contact's full name")
    email: str | None = Field(default=None, description="Contact's email address")
    notes: str | None = Field(default=None, description="Freeform notes stored on the contact")


class ListContactsInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    search: str | None = Field(
        default=None, description="Filter by name or phone number (case-insensitive contains)"
    )
    limit: int | None = Field(
        default=None, description="Number of results to return (default 50, max 200)"
    )
    offset: int | None = Field(default=None, description="Number of results to skip (min 0)")


class GetContactInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    contact_id: str = Field(description="Contact ID")


class UpdateContactInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    contact_id: str = Field(description="Contact ID")
    phone_number: str | None = Field(
        default=None, description="New phone number in E.164 format"
    )
    name: str | None = Field(default=None, description="New contact name")
    email: str | None = Field(default=None, description="New email address")
    notes: str | None = Field(default=None, description="New freeform notes")


class DeleteContactInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    contact_id: str = Field(description="Contact ID")


class GetUsageInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")


class GetUsageDailyInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    days: int | None = Field(default=None, description="Number of days to return (1-365)")


class GetUsageMonthlyInput(BaseModel):
    api_key: str = Field(description="AgentPhone API key (provided by credential system)")
    months: int | None = Field(default=None, description="Number of months to return (1-24)")


# --- Phone number actions --------------------------------------------------


@tool(args_schema=CreateNumberInput)
@serialize_pydantic_return
async def create_number(
    api_key: str,
    country: str | None = None,
    area_code: str | None = None,
    agent_id: str | None = None,
) -> CreateNumberOutput:
    """Provision a new SMS- and voice-enabled phone number."""
    if not api_key or not api_key.strip():
        return CreateNumberOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if country:
        body["country"] = country
    if area_code:
        body["areaCode"] = area_code
    if agent_id:
        body["agentId"] = agent_id

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/numbers", headers=_headers(api_key), json=body
            )
        if not _ok(response):
            return CreateNumberOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return CreateNumberOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateNumberOutput(success=False, error=f"Create phone number failed: {exc}")

    return CreateNumberOutput(
        success=True,
        id=data.get("id"),
        phone_number=data.get("phoneNumber"),
        country=data.get("country"),
        status=data.get("status"),
        type=data.get("type"),
        agent_id=data.get("agentId"),
        created_at=data.get("createdAt"),
    )


@tool(args_schema=ListNumbersInput)
@serialize_pydantic_return
async def list_numbers(
    api_key: str,
    limit: int | None = None,
    offset: int | None = None,
) -> ListNumbersOutput:
    """List all phone numbers provisioned for this AgentPhone account."""
    if not api_key or not api_key.strip():
        return ListNumbersOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/numbers", headers=_headers(api_key), params=params
            )
        if not _ok(response):
            return ListNumbersOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListNumbersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListNumbersOutput(success=False, error=f"List phone numbers failed: {exc}")

    return ListNumbersOutput(
        success=True,
        data=[_phone_number(item) for item in _as_dicts(data.get("data"))],
        has_more=data.get("hasMore"),
        total=data.get("total"),
    )


@tool(args_schema=ReleaseNumberInput)
@serialize_pydantic_return
async def release_number(api_key: str, number_id: str) -> ReleaseNumberOutput:
    """Release (delete) a phone number. This action is irreversible."""
    if not api_key or not api_key.strip():
        return ReleaseNumberOutput(success=False, error=_EMPTY_KEY_ERROR)

    resolved_id = number_id.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API_BASE}/numbers/{resolved_id}", headers=_headers(api_key)
            )
        if not _ok(response):
            return ReleaseNumberOutput(
                success=False, error=_error(response), id=resolved_id, released=False
            )
    except httpx.TimeoutException:
        return ReleaseNumberOutput(
            success=False, error="Request timed out.", id=resolved_id, released=False
        )
    except Exception as exc:
        return ReleaseNumberOutput(
            success=False,
            error=f"Release phone number failed: {exc}",
            id=resolved_id,
            released=False,
        )

    return ReleaseNumberOutput(success=True, id=resolved_id, released=True)


@tool(args_schema=GetNumberMessagesInput)
@serialize_pydantic_return
async def get_number_messages(
    api_key: str,
    number_id: str,
    limit: int | None = None,
    before: str | None = None,
    after: str | None = None,
) -> GetNumberMessagesOutput:
    """Fetch messages received on a specific phone number."""
    if not api_key or not api_key.strip():
        return GetNumberMessagesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if before:
        params["before"] = before
    if after:
        params["after"] = after

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/numbers/{number_id.strip()}/messages",
                headers=_headers(api_key),
                params=params,
            )
        if not _ok(response):
            return GetNumberMessagesOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetNumberMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetNumberMessagesOutput(
            success=False, error=f"Get phone number messages failed: {exc}"
        )

    return GetNumberMessagesOutput(
        success=True,
        data=[_number_message(item) for item in _as_dicts(data.get("data"))],
        has_more=data.get("hasMore"),
    )


# --- Call actions ----------------------------------------------------------


@tool(args_schema=CreateCallInput)
@serialize_pydantic_return
async def create_call(
    api_key: str,
    agent_id: str,
    to_number: str,
    from_number_id: str | None = None,
    initial_greeting: str | None = None,
    voice: str | None = None,
    system_prompt: str | None = None,
) -> CreateCallOutput:
    """Initiate an outbound voice call from an AgentPhone agent."""
    if not api_key or not api_key.strip():
        return CreateCallOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"agentId": agent_id, "toNumber": to_number}
    if from_number_id:
        body["fromNumberId"] = from_number_id
    if initial_greeting:
        body["initialGreeting"] = initial_greeting
    if voice:
        body["voice"] = voice
    if system_prompt:
        body["systemPrompt"] = system_prompt

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/calls", headers=_headers(api_key), json=body
            )
        if not _ok(response):
            return CreateCallOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return CreateCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateCallOutput(success=False, error=f"Create call failed: {exc}")

    return CreateCallOutput(
        success=True,
        id=data.get("id") or data.get("callId"),
        agent_id=data.get("agentId"),
        status=data.get("status"),
        to_number=data.get("toNumber"),
        from_number=data.get("fromNumber"),
        phone_number_id=data.get("phoneNumberId"),
        direction=data.get("direction"),
        started_at=data.get("startedAt"),
    )


@tool(args_schema=ListCallsInput)
@serialize_pydantic_return
async def list_calls(
    api_key: str,
    limit: int | None = None,
    offset: int | None = None,
    status: str | None = None,
    direction: str | None = None,
    type: str | None = None,
    search: str | None = None,
) -> ListCallsOutput:
    """List voice calls for this AgentPhone account."""
    if not api_key or not api_key.strip():
        return ListCallsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset
    if status:
        params["status"] = status
    if direction:
        params["direction"] = direction
    if type:
        params["type"] = type
    if search:
        params["search"] = search

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/calls", headers=_headers(api_key), params=params
            )
        if not _ok(response):
            return ListCallsOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListCallsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListCallsOutput(success=False, error=f"List calls failed: {exc}")

    # TODO (unverified): the published OpenAPI declares the 200 body of
    # GET /v1/calls as "Any type", so the row fields below (recordingUrl,
    # recordingAvailable, lastTranscriptSnippet) are read permissively per
    # https://docs.agentphone.ai/api-reference/calls/list-calls-v-1-calls-get
    return ListCallsOutput(
        success=True,
        data=[_call_summary(item) for item in _as_dicts(data.get("data"))],
        has_more=data.get("hasMore"),
        total=data.get("total"),
    )


@tool(args_schema=GetCallInput)
@serialize_pydantic_return
async def get_call(api_key: str, call_id: str) -> GetCallOutput:
    """Fetch a call and its full transcript."""
    if not api_key or not api_key.strip():
        return GetCallOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/calls/{call_id.strip()}", headers=_headers(api_key)
            )
        if not _ok(response):
            return GetCallOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetCallOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCallOutput(success=False, error=f"Get call failed: {exc}")

    # TODO (unverified): the published OpenAPI declares the 200 body of
    # GET /v1/calls/{call_id} as "Any type"; the transcripts[] turn fields
    # (transcript, confidence, response) are read permissively per
    # https://docs.agentphone.ai/api-reference/calls/get-call-v-1-calls-call-id-get
    return GetCallOutput(
        success=True,
        id=data.get("id"),
        agent_id=data.get("agentId"),
        phone_number_id=data.get("phoneNumberId"),
        phone_number=data.get("phoneNumber"),
        from_number=data.get("fromNumber"),
        to_number=data.get("toNumber"),
        direction=data.get("direction"),
        status=data.get("status"),
        started_at=data.get("startedAt"),
        ended_at=data.get("endedAt"),
        duration_seconds=data.get("durationSeconds"),
        last_transcript_snippet=data.get("lastTranscriptSnippet"),
        recording_url=data.get("recordingUrl"),
        recording_available=data.get("recordingAvailable"),
        transcripts=[_transcript_turn(item) for item in _as_dicts(data.get("transcripts"))],
    )


@tool(args_schema=GetCallTranscriptInput)
@serialize_pydantic_return
async def get_call_transcript(api_key: str, call_id: str) -> GetCallTranscriptOutput:
    """Get the full ordered transcript for a call."""
    if not api_key or not api_key.strip():
        return GetCallTranscriptOutput(success=False, error=_EMPTY_KEY_ERROR)

    resolved_id = call_id.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/calls/{resolved_id}/transcript", headers=_headers(api_key)
            )
        if not _ok(response):
            return GetCallTranscriptOutput(
                success=False, error=_error(response), call_id=resolved_id
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCallTranscriptOutput(
            success=False, error="Request timed out.", call_id=resolved_id
        )
    except Exception as exc:
        return GetCallTranscriptOutput(
            success=False, error=f"Get call transcript failed: {exc}", call_id=resolved_id
        )

    # The endpoint returns either {"callId": ..., "transcript": [...]} or a
    # bare list of turns.
    # TODO (unverified): GET /v1/calls/{call_id}/transcript is documented as
    # available, but its turn shape (role/content/createdAt) is not published
    # in the API reference index at https://docs.agentphone.ai/llms.txt — both
    # payload shapes are therefore handled defensively.
    if isinstance(data, dict):
        raw_turns = data.get("transcript")
        reported_id = data.get("callId") or resolved_id
    else:
        raw_turns = data
        reported_id = resolved_id

    return GetCallTranscriptOutput(
        success=True,
        call_id=reported_id,
        transcript=[_transcript_entry(item) for item in _as_dicts(raw_turns)],
    )


# --- Conversation actions --------------------------------------------------


@tool(args_schema=ListConversationsInput)
@serialize_pydantic_return
async def list_conversations(
    api_key: str,
    limit: int | None = None,
    offset: int | None = None,
) -> ListConversationsOutput:
    """List conversations (message threads) for this AgentPhone account."""
    if not api_key or not api_key.strip():
        return ListConversationsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/conversations", headers=_headers(api_key), params=params
            )
        if not _ok(response):
            return ListConversationsOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListConversationsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListConversationsOutput(success=False, error=f"List conversations failed: {exc}")

    return ListConversationsOutput(
        success=True,
        data=[_conversation_summary(item) for item in _as_dicts(data.get("data"))],
        has_more=data.get("hasMore"),
        total=data.get("total"),
    )


@tool(args_schema=GetConversationInput)
@serialize_pydantic_return
async def get_conversation(
    api_key: str,
    conversation_id: str,
    message_limit: int | None = None,
) -> GetConversationOutput:
    """Get a conversation along with its recent messages."""
    if not api_key or not api_key.strip():
        return GetConversationOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if message_limit is not None:
        params["message_limit"] = message_limit

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/conversations/{conversation_id.strip()}",
                headers=_headers(api_key),
                params=params,
            )
        if not _ok(response):
            return GetConversationOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetConversationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetConversationOutput(success=False, error=f"Get conversation failed: {exc}")

    return GetConversationOutput(
        success=True,
        id=data.get("id"),
        agent_id=data.get("agentId"),
        phone_number_id=data.get("phoneNumberId"),
        phone_number=data.get("phoneNumber"),
        participant=data.get("participant"),
        last_message_at=data.get("lastMessageAt"),
        message_count=data.get("messageCount"),
        metadata=data.get("metadata"),
        created_at=data.get("createdAt"),
        messages=[_conversation_message(item) for item in _as_dicts(data.get("messages"))],
    )


@tool(args_schema=UpdateConversationInput)
@serialize_pydantic_return
async def update_conversation(
    api_key: str,
    conversation_id: str,
    metadata: dict[str, Any] | None = None,
    clear_metadata: bool = False,
) -> UpdateConversationOutput:
    """Update the custom metadata stored on a conversation."""
    if not api_key or not api_key.strip():
        return UpdateConversationOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if clear_metadata:
        body["metadata"] = None
    elif metadata is not None:
        body["metadata"] = metadata

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_API_BASE}/conversations/{conversation_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if not _ok(response):
            return UpdateConversationOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return UpdateConversationOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateConversationOutput(
            success=False, error=f"Update conversation failed: {exc}"
        )

    return UpdateConversationOutput(
        success=True,
        id=data.get("id"),
        agent_id=data.get("agentId"),
        phone_number_id=data.get("phoneNumberId"),
        phone_number=data.get("phoneNumber"),
        participant=data.get("participant"),
        last_message_at=data.get("lastMessageAt"),
        message_count=data.get("messageCount"),
        metadata=data.get("metadata"),
        created_at=data.get("createdAt"),
        messages=[_conversation_message(item) for item in _as_dicts(data.get("messages"))],
    )


@tool(args_schema=GetConversationMessagesInput)
@serialize_pydantic_return
async def get_conversation_messages(
    api_key: str,
    conversation_id: str,
    limit: int | None = None,
    before: str | None = None,
    after: str | None = None,
) -> GetConversationMessagesOutput:
    """Get paginated messages for a conversation."""
    if not api_key or not api_key.strip():
        return GetConversationMessagesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if before:
        params["before"] = before
    if after:
        params["after"] = after

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/conversations/{conversation_id.strip()}/messages",
                headers=_headers(api_key),
                params=params,
            )
        if not _ok(response):
            return GetConversationMessagesOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetConversationMessagesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetConversationMessagesOutput(
            success=False, error=f"Get conversation messages failed: {exc}"
        )

    return GetConversationMessagesOutput(
        success=True,
        data=[_conversation_message(item) for item in _as_dicts(data.get("data"))],
        has_more=data.get("hasMore"),
    )


# --- Message actions -------------------------------------------------------


@tool(args_schema=SendMessageInput)
@serialize_pydantic_return
async def send_message(
    api_key: str,
    agent_id: str,
    to_number: str,
    body: str,
    media_url: str | None = None,
    media_urls: list[str] | None = None,
    number_id: str | None = None,
) -> SendMessageOutput:
    """Send an outbound SMS or iMessage from an AgentPhone agent."""
    if not api_key or not api_key.strip():
        return SendMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    payload: dict[str, Any] = {
        "agent_id": agent_id,
        "to_number": to_number,
        "body": body,
    }
    if media_url:
        payload["media_url"] = media_url
    if media_urls:
        payload["media_urls"] = media_urls
    if number_id:
        payload["number_id"] = number_id

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/messages", headers=_headers(api_key), json=payload
            )
        if not _ok(response):
            return SendMessageOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return SendMessageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return SendMessageOutput(success=False, error=f"Send message failed: {exc}")

    return SendMessageOutput(
        success=True,
        id=data.get("id"),
        status=data.get("status"),
        channel=data.get("channel"),
        from_number=data.get("from_number"),
        to_number=data.get("to_number"),
    )


@tool(args_schema=ReactToMessageInput)
@serialize_pydantic_return
async def react_to_message(
    api_key: str,
    message_id: str,
    reaction: str,
) -> ReactToMessageOutput:
    """Send an iMessage tapback reaction to a message (iMessage only)."""
    if not api_key or not api_key.strip():
        return ReactToMessageOutput(success=False, error=_EMPTY_KEY_ERROR)

    resolved_id = message_id.strip()
    body: dict[str, Any] = {"reaction": reaction}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/messages/{resolved_id}/reactions",
                headers=_headers(api_key),
                json=body,
            )
        if not _ok(response):
            return ReactToMessageOutput(
                success=False, error=_error(response), message_id=resolved_id
            )
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ReactToMessageOutput(
            success=False, error="Request timed out.", message_id=resolved_id
        )
    except Exception as exc:
        return ReactToMessageOutput(
            success=False, error=f"React to message failed: {exc}", message_id=resolved_id
        )

    return ReactToMessageOutput(
        success=True,
        id=data.get("id"),
        reaction_type=data.get("reaction_type"),
        message_id=data.get("message_id") or resolved_id,
        channel=data.get("channel"),
    )


# --- Contact actions -------------------------------------------------------


@tool(args_schema=CreateContactInput)
@serialize_pydantic_return
async def create_contact(
    api_key: str,
    phone_number: str,
    name: str,
    email: str | None = None,
    notes: str | None = None,
) -> CreateContactOutput:
    """Create a new contact in AgentPhone."""
    if not api_key or not api_key.strip():
        return CreateContactOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"phoneNumber": phone_number, "name": name}
    if email:
        body["email"] = email
    if notes:
        body["notes"] = notes

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_API_BASE}/contacts", headers=_headers(api_key), json=body
            )
        if not _ok(response):
            return CreateContactOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return CreateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateContactOutput(success=False, error=f"Create contact failed: {exc}")

    return CreateContactOutput(
        success=True,
        id=data.get("id"),
        phone_number=data.get("phoneNumber"),
        name=data.get("name"),
        email=data.get("email"),
        notes=data.get("notes"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=ListContactsInput)
@serialize_pydantic_return
async def list_contacts(
    api_key: str,
    search: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> ListContactsOutput:
    """List contacts for this AgentPhone account."""
    if not api_key or not api_key.strip():
        return ListContactsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if search:
        params["search"] = search
    if limit is not None:
        params["limit"] = limit
    if offset is not None:
        params["offset"] = offset

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/contacts", headers=_headers(api_key), params=params
            )
        if not _ok(response):
            return ListContactsOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return ListContactsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListContactsOutput(success=False, error=f"List contacts failed: {exc}")

    return ListContactsOutput(
        success=True,
        data=[_contact(item) for item in _as_dicts(data.get("data"))],
        has_more=data.get("hasMore"),
        total=data.get("total"),
    )


@tool(args_schema=GetContactInput)
@serialize_pydantic_return
async def get_contact(api_key: str, contact_id: str) -> GetContactOutput:
    """Fetch a single contact by ID."""
    if not api_key or not api_key.strip():
        return GetContactOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/contacts/{contact_id.strip()}", headers=_headers(api_key)
            )
        if not _ok(response):
            return GetContactOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetContactOutput(success=False, error=f"Get contact failed: {exc}")

    return GetContactOutput(
        success=True,
        id=data.get("id"),
        phone_number=data.get("phoneNumber"),
        name=data.get("name"),
        email=data.get("email"),
        notes=data.get("notes"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=UpdateContactInput)
@serialize_pydantic_return
async def update_contact(
    api_key: str,
    contact_id: str,
    phone_number: str | None = None,
    name: str | None = None,
    email: str | None = None,
    notes: str | None = None,
) -> UpdateContactOutput:
    """Update a contact's fields."""
    if not api_key or not api_key.strip():
        return UpdateContactOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if phone_number:
        body["phoneNumber"] = phone_number
    if name:
        body["name"] = name
    if email:
        body["email"] = email
    if notes:
        body["notes"] = notes

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_API_BASE}/contacts/{contact_id.strip()}",
                headers=_headers(api_key),
                json=body,
            )
        if not _ok(response):
            return UpdateContactOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return UpdateContactOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateContactOutput(success=False, error=f"Update contact failed: {exc}")

    return UpdateContactOutput(
        success=True,
        id=data.get("id"),
        phone_number=data.get("phoneNumber"),
        name=data.get("name"),
        email=data.get("email"),
        notes=data.get("notes"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=DeleteContactInput)
@serialize_pydantic_return
async def delete_contact(api_key: str, contact_id: str) -> DeleteContactOutput:
    """Delete a contact by ID."""
    if not api_key or not api_key.strip():
        return DeleteContactOutput(success=False, error=_EMPTY_KEY_ERROR)

    resolved_id = contact_id.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_API_BASE}/contacts/{resolved_id}", headers=_headers(api_key)
            )
        if not _ok(response):
            return DeleteContactOutput(
                success=False, error=_error(response), id=resolved_id, deleted=False
            )
    except httpx.TimeoutException:
        return DeleteContactOutput(
            success=False, error="Request timed out.", id=resolved_id, deleted=False
        )
    except Exception as exc:
        return DeleteContactOutput(
            success=False, error=f"Delete contact failed: {exc}", id=resolved_id, deleted=False
        )

    return DeleteContactOutput(success=True, id=resolved_id, deleted=True)


# --- Usage actions ---------------------------------------------------------


@tool(args_schema=GetUsageInput)
@serialize_pydantic_return
async def get_usage(api_key: str) -> GetUsageOutput:
    """Retrieve current usage statistics for the AgentPhone account."""
    if not api_key or not api_key.strip():
        return GetUsageOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_API_BASE}/usage", headers=_headers(api_key))
        if not _ok(response):
            return GetUsageOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetUsageOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetUsageOutput(success=False, error=f"Get usage failed: {exc}")

    raw_plan = _as_dict(data.get("plan"))
    raw_limits = _as_dict(raw_plan.get("limits"))
    raw_numbers = _as_dict(data.get("numbers"))
    raw_stats = _as_dict(data.get("stats"))

    return GetUsageOutput(
        success=True,
        plan=UsagePlan(
            name=raw_plan.get("name"),
            limits=UsagePlanLimits(
                numbers=raw_limits.get("numbers"),
                messages_per_month=raw_limits.get("messagesPerMonth"),
                voice_minutes_per_month=raw_limits.get("voiceMinutesPerMonth"),
                max_call_duration_minutes=raw_limits.get("maxCallDurationMinutes"),
                concurrent_calls=raw_limits.get("concurrentCalls"),
            ),
        ),
        numbers=UsageNumbers(
            used=raw_numbers.get("used"),
            limit=raw_numbers.get("limit"),
            remaining=raw_numbers.get("remaining"),
        ),
        stats=UsageStats(
            total_messages=raw_stats.get("totalMessages"),
            messages_last_24h=raw_stats.get("messagesLast24h"),
            messages_last_7d=raw_stats.get("messagesLast7d"),
            messages_last_30d=raw_stats.get("messagesLast30d"),
            total_calls=raw_stats.get("totalCalls"),
            calls_last_24h=raw_stats.get("callsLast24h"),
            calls_last_7d=raw_stats.get("callsLast7d"),
            calls_last_30d=raw_stats.get("callsLast30d"),
            total_webhook_deliveries=raw_stats.get("totalWebhookDeliveries"),
            successful_webhook_deliveries=raw_stats.get("successfulWebhookDeliveries"),
            failed_webhook_deliveries=raw_stats.get("failedWebhookDeliveries"),
        ),
        period_start=data.get("periodStart"),
        period_end=data.get("periodEnd"),
    )


@tool(args_schema=GetUsageDailyInput)
@serialize_pydantic_return
async def get_usage_daily(api_key: str, days: int | None = None) -> GetUsageDailyOutput:
    """Get a daily breakdown of usage (messages, calls, webhooks)."""
    if not api_key or not api_key.strip():
        return GetUsageDailyOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if days is not None:
        params["days"] = days

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/usage/daily", headers=_headers(api_key), params=params
            )
        if not _ok(response):
            return GetUsageDailyOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetUsageDailyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetUsageDailyOutput(success=False, error=f"Get daily usage failed: {exc}")

    return GetUsageDailyOutput(
        success=True,
        data=[
            UsageDailyEntry(
                date=entry.get("date"),
                messages=entry.get("messages"),
                calls=entry.get("calls"),
                webhooks=entry.get("webhooks"),
            )
            for entry in _as_dicts(data.get("data"))
        ],
        days=data.get("days"),
    )


@tool(args_schema=GetUsageMonthlyInput)
@serialize_pydantic_return
async def get_usage_monthly(api_key: str, months: int | None = None) -> GetUsageMonthlyOutput:
    """Get monthly usage aggregation (messages, calls, webhooks)."""
    if not api_key or not api_key.strip():
        return GetUsageMonthlyOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if months is not None:
        params["months"] = months

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_API_BASE}/usage/monthly", headers=_headers(api_key), params=params
            )
        if not _ok(response):
            return GetUsageMonthlyOutput(success=False, error=_error(response))
        data = _as_dict(response.json())
    except httpx.TimeoutException:
        return GetUsageMonthlyOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetUsageMonthlyOutput(success=False, error=f"Get monthly usage failed: {exc}")

    return GetUsageMonthlyOutput(
        success=True,
        data=[
            UsageMonthlyEntry(
                month=entry.get("month"),
                messages=entry.get("messages"),
                calls=entry.get("calls"),
                webhooks=entry.get("webhooks"),
            )
            for entry in _as_dicts(data.get("data"))
        ],
        months=data.get("months"),
    )
