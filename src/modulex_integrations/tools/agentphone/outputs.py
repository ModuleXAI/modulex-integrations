"""Pydantic response models for the AgentPhone integration's @tool functions.

AgentPhone follows the *api_key* runtime convention: each ``@tool``
function takes an ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it from the resolved credential.

Error model: the AgentPhone REST API returns proper HTTP status codes,
but every tool wraps the call so non-2xx responses, timeouts, and
unexpected exceptions surface as ``success=False`` + ``error`` rather
than raising. Every output model carries both shapes; data fields stay
permissive (``<type> | None``) because responses are read with
``.get()``.

Field names are snake_case; the upstream API mixes camelCase
(``phoneNumber``, ``hasMore``) and snake_case (``from_number``,
``reaction_type``) keys, which are normalized at parse time in
``tools.py``.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CallSummary",
    "Contact",
    "ConversationMessage",
    "ConversationSummary",
    "CreateCallOutput",
    "CreateContactOutput",
    "CreateNumberOutput",
    "DeleteContactOutput",
    "GetCallOutput",
    "GetCallTranscriptOutput",
    "GetContactOutput",
    "GetConversationMessagesOutput",
    "GetConversationOutput",
    "GetNumberMessagesOutput",
    "GetUsageDailyOutput",
    "GetUsageMonthlyOutput",
    "GetUsageOutput",
    "ListCallsOutput",
    "ListContactsOutput",
    "ListConversationsOutput",
    "ListNumbersOutput",
    "NumberMessage",
    "PhoneNumberSummary",
    "ReactToMessageOutput",
    "ReleaseNumberOutput",
    "SendMessageOutput",
    "TranscriptEntry",
    "TranscriptTurn",
    "UpdateContactOutput",
    "UpdateConversationOutput",
    "UsageDailyEntry",
    "UsageMonthlyEntry",
    "UsageNumbers",
    "UsagePlan",
    "UsagePlanLimits",
    "UsageStats",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class PhoneNumberSummary(_Base):
    """A single provisioned phone number row."""

    id: str | None = None
    phone_number: str | None = None
    country: str | None = None
    status: str | None = None
    type: str | None = None
    agent_id: str | None = None
    created_at: str | None = None


class NumberMessage(_Base):
    """A message received on a phone number.

    The upstream payload spells the sender key ``from_`` (trailing
    underscore) and the recipient key ``to``.
    """

    id: str | None = None
    from_: str | None = None
    to: str | None = None
    body: str | None = None
    direction: str | None = None
    channel: str | None = None
    received_at: str | None = None


class CallSummary(_Base):
    """A single call row in ``list_calls``."""

    id: str | None = None
    agent_id: str | None = None
    phone_number_id: str | None = None
    phone_number: str | None = None
    from_number: str | None = None
    to_number: str | None = None
    direction: str | None = None
    status: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: float | None = None
    last_transcript_snippet: str | None = None
    recording_url: str | None = None
    recording_available: bool | None = None


class TranscriptTurn(_Base):
    """One transcript turn as returned inline on a call detail."""

    id: str | None = None
    transcript: str | None = None
    confidence: float | None = None
    response: str | None = None
    created_at: str | None = None


class TranscriptEntry(_Base):
    """One flat transcript turn from the dedicated transcript endpoint."""

    role: str | None = None
    content: str | None = None
    created_at: str | None = None


class ConversationSummary(_Base):
    """A single conversation row in ``list_conversations``."""

    id: str | None = None
    agent_id: str | None = None
    phone_number_id: str | None = None
    phone_number: str | None = None
    participant: str | None = None
    last_message_at: str | None = None
    last_message_preview: str | None = None
    message_count: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None


class ConversationMessage(_Base):
    """A single message inside a conversation."""

    id: str | None = None
    body: str | None = None
    from_number: str | None = None
    to_number: str | None = None
    direction: str | None = None
    channel: str | None = None
    media_url: str | None = None
    media_urls: list[str] = Field(default_factory=list)
    received_at: str | None = None


class Contact(_Base):
    """A single contact row."""

    id: str | None = None
    phone_number: str | None = None
    name: str | None = None
    email: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class UsagePlanLimits(_Base):
    """Plan limits reported by the usage endpoint."""

    numbers: int | None = None
    messages_per_month: int | None = None
    voice_minutes_per_month: int | None = None
    max_call_duration_minutes: int | None = None
    concurrent_calls: int | None = None


class UsagePlan(_Base):
    """Plan name plus its limits."""

    name: str | None = None
    limits: UsagePlanLimits | None = None


class UsageNumbers(_Base):
    """Phone-number consumption against the plan limit."""

    used: int | None = None
    limit: int | None = None
    remaining: int | None = None


class UsageStats(_Base):
    """Aggregated message, call, and webhook counters."""

    total_messages: int | None = None
    messages_last_24h: int | None = None
    messages_last_7d: int | None = None
    messages_last_30d: int | None = None
    total_calls: int | None = None
    calls_last_24h: int | None = None
    calls_last_7d: int | None = None
    calls_last_30d: int | None = None
    total_webhook_deliveries: int | None = None
    successful_webhook_deliveries: int | None = None
    failed_webhook_deliveries: int | None = None


class UsageDailyEntry(_Base):
    """One day of usage."""

    date: str | None = None
    messages: int | None = None
    calls: int | None = None
    webhooks: int | None = None


class UsageMonthlyEntry(_Base):
    """One month of usage."""

    month: str | None = None
    messages: int | None = None
    calls: int | None = None
    webhooks: int | None = None


# --- Phone number actions --------------------------------------------------


class CreateNumberOutput(_Base):
    """Result of ``create_number``."""

    success: bool
    error: str | None = None
    id: str | None = None
    phone_number: str | None = None
    country: str | None = None
    status: str | None = None
    type: str | None = None
    agent_id: str | None = None
    created_at: str | None = None


class ListNumbersOutput(_Base):
    """Result of ``list_numbers``."""

    success: bool
    error: str | None = None
    data: list[PhoneNumberSummary] = Field(default_factory=list)
    has_more: bool | None = None
    total: int | None = None


class ReleaseNumberOutput(_Base):
    """Result of ``release_number``."""

    success: bool
    error: str | None = None
    id: str | None = None
    released: bool | None = None


class GetNumberMessagesOutput(_Base):
    """Result of ``get_number_messages``."""

    success: bool
    error: str | None = None
    data: list[NumberMessage] = Field(default_factory=list)
    has_more: bool | None = None


# --- Call actions ----------------------------------------------------------


class CreateCallOutput(_Base):
    """Result of ``create_call``."""

    success: bool
    error: str | None = None
    id: str | None = None
    agent_id: str | None = None
    status: str | None = None
    to_number: str | None = None
    from_number: str | None = None
    phone_number_id: str | None = None
    direction: str | None = None
    started_at: str | None = None


class ListCallsOutput(_Base):
    """Result of ``list_calls``."""

    success: bool
    error: str | None = None
    data: list[CallSummary] = Field(default_factory=list)
    has_more: bool | None = None
    total: int | None = None


class GetCallOutput(_Base):
    """Result of ``get_call`` — a call detail with its transcript turns."""

    success: bool
    error: str | None = None
    id: str | None = None
    agent_id: str | None = None
    phone_number_id: str | None = None
    phone_number: str | None = None
    from_number: str | None = None
    to_number: str | None = None
    direction: str | None = None
    status: str | None = None
    started_at: str | None = None
    ended_at: str | None = None
    duration_seconds: float | None = None
    last_transcript_snippet: str | None = None
    recording_url: str | None = None
    recording_available: bool | None = None
    transcripts: list[TranscriptTurn] = Field(default_factory=list)


class GetCallTranscriptOutput(_Base):
    """Result of ``get_call_transcript``."""

    success: bool
    error: str | None = None
    call_id: str | None = None
    transcript: list[TranscriptEntry] = Field(default_factory=list)


# --- Conversation actions --------------------------------------------------


class ListConversationsOutput(_Base):
    """Result of ``list_conversations``."""

    success: bool
    error: str | None = None
    data: list[ConversationSummary] = Field(default_factory=list)
    has_more: bool | None = None
    total: int | None = None


class GetConversationOutput(_Base):
    """Result of ``get_conversation``."""

    success: bool
    error: str | None = None
    id: str | None = None
    agent_id: str | None = None
    phone_number_id: str | None = None
    phone_number: str | None = None
    participant: str | None = None
    last_message_at: str | None = None
    message_count: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)


class UpdateConversationOutput(_Base):
    """Result of ``update_conversation``."""

    success: bool
    error: str | None = None
    id: str | None = None
    agent_id: str | None = None
    phone_number_id: str | None = None
    phone_number: str | None = None
    participant: str | None = None
    last_message_at: str | None = None
    message_count: int | None = None
    metadata: dict[str, Any] | None = None
    created_at: str | None = None
    messages: list[ConversationMessage] = Field(default_factory=list)


class GetConversationMessagesOutput(_Base):
    """Result of ``get_conversation_messages``."""

    success: bool
    error: str | None = None
    data: list[ConversationMessage] = Field(default_factory=list)
    has_more: bool | None = None


# --- Message actions -------------------------------------------------------


class SendMessageOutput(_Base):
    """Result of ``send_message``."""

    success: bool
    error: str | None = None
    id: str | None = None
    status: str | None = None
    channel: str | None = None
    from_number: str | None = None
    to_number: str | None = None


class ReactToMessageOutput(_Base):
    """Result of ``react_to_message``."""

    success: bool
    error: str | None = None
    id: str | None = None
    reaction_type: str | None = None
    message_id: str | None = None
    channel: str | None = None


# --- Contact actions -------------------------------------------------------


class CreateContactOutput(_Base):
    """Result of ``create_contact``."""

    success: bool
    error: str | None = None
    id: str | None = None
    phone_number: str | None = None
    name: str | None = None
    email: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ListContactsOutput(_Base):
    """Result of ``list_contacts``."""

    success: bool
    error: str | None = None
    data: list[Contact] = Field(default_factory=list)
    has_more: bool | None = None
    total: int | None = None


class GetContactOutput(_Base):
    """Result of ``get_contact``."""

    success: bool
    error: str | None = None
    id: str | None = None
    phone_number: str | None = None
    name: str | None = None
    email: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class UpdateContactOutput(_Base):
    """Result of ``update_contact``."""

    success: bool
    error: str | None = None
    id: str | None = None
    phone_number: str | None = None
    name: str | None = None
    email: str | None = None
    notes: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DeleteContactOutput(_Base):
    """Result of ``delete_contact``."""

    success: bool
    error: str | None = None
    id: str | None = None
    deleted: bool | None = None


# --- Usage actions ---------------------------------------------------------


class GetUsageOutput(_Base):
    """Result of ``get_usage``."""

    success: bool
    error: str | None = None
    plan: UsagePlan | None = None
    numbers: UsageNumbers | None = None
    stats: UsageStats | None = None
    period_start: str | None = None
    period_end: str | None = None


class GetUsageDailyOutput(_Base):
    """Result of ``get_usage_daily``."""

    success: bool
    error: str | None = None
    data: list[UsageDailyEntry] = Field(default_factory=list)
    days: int | None = None


class GetUsageMonthlyOutput(_Base):
    """Result of ``get_usage_monthly``."""

    success: bool
    error: str | None = None
    data: list[UsageMonthlyEntry] = Field(default_factory=list)
    months: int | None = None
