"""Pydantic response models for the help_scout integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddNoteOutput",
    "ConversationDetail",
    "CreateCustomerOutput",
    "GetConversationDetailsOutput",
    "GetConversationThreadsOutput",
    "GetTagByIdOutput",
    "ListTagsOutput",
    "PaginationInfo",
    "SendReplyOutput",
    "TagItem",
    "ThreadItem",
    "UpdateConversationOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class PaginationInfo(_Base):
    size: int | None = None
    total_elements: int | None = None
    total_pages: int | None = None
    number: int | None = None


class TagItem(_Base):
    id: int | None = None
    name: str | None = None
    slug: str | None = None
    color: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    ticket_count: int | None = None


class ThreadItem(_Base):
    id: int | None = None
    type: str | None = None
    status: str | None = None
    state: str | None = None
    body: str | None = None
    source: dict[str, Any] | None = None
    customer: dict[str, Any] | None = None
    created_by: dict[str, Any] | None = None
    assigned_to: dict[str, Any] | None = None
    created_at: str | None = None


class ConversationDetail(_Base):
    id: int | None = None
    number: int | None = None
    subject: str | None = None
    status: str | None = None
    mailbox_id: int | None = None
    primary_customer: dict[str, Any] | None = None
    threads: list[dict[str, Any]] = Field(default_factory=list)
    tags: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None


# --- Per-action output models ---------------------------------------------


class AddNoteOutput(_Base):
    success: bool
    error: str | None = None
    conversation_id: str | None = None


class CreateCustomerOutput(_Base):
    success: bool
    error: str | None = None
    customer_id: str | None = None


class GetConversationDetailsOutput(_Base):
    success: bool
    error: str | None = None
    conversation: ConversationDetail | None = None


class GetConversationThreadsOutput(_Base):
    success: bool
    error: str | None = None
    threads: list[ThreadItem] = Field(default_factory=list)
    pagination: PaginationInfo | None = None


class GetTagByIdOutput(_Base):
    success: bool
    error: str | None = None
    tag: TagItem | None = None


class ListTagsOutput(_Base):
    success: bool
    error: str | None = None
    tags: list[TagItem] = Field(default_factory=list)
    pagination: PaginationInfo | None = None


class SendReplyOutput(_Base):
    success: bool
    error: str | None = None
    conversation_id: str | None = None


class UpdateConversationOutput(_Base):
    success: bool
    error: str | None = None
    conversation_id: str | None = None
