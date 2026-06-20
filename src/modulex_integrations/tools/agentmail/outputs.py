"""Pydantic response models for the AgentMail integration's @tool functions.

AgentMail follows the *api_key* runtime convention: each ``@tool``
function takes an ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it from the resolved credential.

Error model: the AgentMail REST API returns proper HTTP status codes,
but every tool wraps the call so non-2xx responses, timeouts, and
unexpected exceptions surface as ``success=False`` + ``error`` rather
than raising. Every output model carries both shapes; data fields stay
permissive (``<type> | None``) because the API is read with ``.get()``.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateDraftOutput",
    "CreateInboxOutput",
    "DeleteDraftOutput",
    "DeleteInboxOutput",
    "DeleteThreadOutput",
    "DraftSummary",
    "ForwardMessageOutput",
    "GetDraftOutput",
    "GetInboxOutput",
    "GetMessageOutput",
    "GetThreadOutput",
    "InboxSummary",
    "ListDraftsOutput",
    "ListInboxesOutput",
    "ListMessagesOutput",
    "ListThreadsOutput",
    "MessageSummary",
    "ReplyMessageOutput",
    "SendDraftOutput",
    "SendMessageOutput",
    "ThreadMessage",
    "ThreadSummary",
    "UpdateDraftOutput",
    "UpdateInboxOutput",
    "UpdateMessageOutput",
    "UpdateThreadOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class InboxSummary(_Base):
    """A single inbox row in ``list_inboxes``."""

    inbox_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ThreadSummary(_Base):
    """A single thread row in ``list_threads``."""

    thread_id: str | None = None
    subject: str | None = None
    senders: list[str] = Field(default_factory=list)
    recipients: list[str] = Field(default_factory=list)
    message_count: int | None = None
    last_message_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ThreadMessage(_Base):
    """A single message inside ``get_thread``."""

    message_id: str | None = None
    from_: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    subject: str | None = None
    text: str | None = None
    html: str | None = None
    labels: list[str] = Field(default_factory=list)
    timestamp: str | None = None
    created_at: str | None = None


class MessageSummary(_Base):
    """A single message row in ``list_messages``."""

    message_id: str | None = None
    from_: str | None = None
    to: list[str] = Field(default_factory=list)
    subject: str | None = None
    preview: str | None = None
    timestamp: str | None = None
    created_at: str | None = None


class DraftSummary(_Base):
    """A single draft row in ``list_drafts``."""

    draft_id: str | None = None
    inbox_id: str | None = None
    subject: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    preview: str | None = None
    send_status: str | None = None
    send_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


# --- Inbox action outputs --------------------------------------------------


class CreateInboxOutput(_Base):
    success: bool
    error: str | None = None
    inbox_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ListInboxesOutput(_Base):
    success: bool
    error: str | None = None
    inboxes: list[InboxSummary] = Field(default_factory=list)
    count: int | None = None
    next_page_token: str | None = None


class GetInboxOutput(_Base):
    success: bool
    error: str | None = None
    inbox_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class UpdateInboxOutput(_Base):
    success: bool
    error: str | None = None
    inbox_id: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class DeleteInboxOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


# --- Message action outputs ------------------------------------------------


class SendMessageOutput(_Base):
    success: bool
    error: str | None = None
    thread_id: str | None = None
    message_id: str | None = None
    subject: str | None = None
    to: str | None = None


class ReplyMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    thread_id: str | None = None


class ForwardMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    thread_id: str | None = None


class ListMessagesOutput(_Base):
    success: bool
    error: str | None = None
    messages: list[MessageSummary] = Field(default_factory=list)
    count: int | None = None
    next_page_token: str | None = None


class GetMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    thread_id: str | None = None
    from_: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    subject: str | None = None
    text: str | None = None
    html: str | None = None
    labels: list[str] = Field(default_factory=list)
    timestamp: str | None = None
    created_at: str | None = None


class UpdateMessageOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    labels: list[str] = Field(default_factory=list)


# --- Thread action outputs -------------------------------------------------


class ListThreadsOutput(_Base):
    success: bool
    error: str | None = None
    threads: list[ThreadSummary] = Field(default_factory=list)
    count: int | None = None
    next_page_token: str | None = None


class GetThreadOutput(_Base):
    success: bool
    error: str | None = None
    thread_id: str | None = None
    subject: str | None = None
    senders: list[str] = Field(default_factory=list)
    recipients: list[str] = Field(default_factory=list)
    message_count: int | None = None
    labels: list[str] = Field(default_factory=list)
    last_message_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    messages: list[ThreadMessage] = Field(default_factory=list)


class UpdateThreadOutput(_Base):
    success: bool
    error: str | None = None
    thread_id: str | None = None
    labels: list[str] = Field(default_factory=list)


class DeleteThreadOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


# --- Draft action outputs --------------------------------------------------


class CreateDraftOutput(_Base):
    success: bool
    error: str | None = None
    draft_id: str | None = None
    inbox_id: str | None = None
    subject: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    text: str | None = None
    html: str | None = None
    preview: str | None = None
    labels: list[str] = Field(default_factory=list)
    in_reply_to: str | None = None
    send_status: str | None = None
    send_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class UpdateDraftOutput(_Base):
    success: bool
    error: str | None = None
    draft_id: str | None = None
    inbox_id: str | None = None
    subject: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    text: str | None = None
    html: str | None = None
    preview: str | None = None
    labels: list[str] = Field(default_factory=list)
    in_reply_to: str | None = None
    send_status: str | None = None
    send_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class GetDraftOutput(_Base):
    success: bool
    error: str | None = None
    draft_id: str | None = None
    inbox_id: str | None = None
    subject: str | None = None
    to: list[str] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    text: str | None = None
    html: str | None = None
    preview: str | None = None
    labels: list[str] = Field(default_factory=list)
    in_reply_to: str | None = None
    send_status: str | None = None
    send_at: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ListDraftsOutput(_Base):
    success: bool
    error: str | None = None
    drafts: list[DraftSummary] = Field(default_factory=list)
    count: int | None = None
    next_page_token: str | None = None


class DeleteDraftOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class SendDraftOutput(_Base):
    success: bool
    error: str | None = None
    message_id: str | None = None
    thread_id: str | None = None
