"""Pydantic response models for the Intercom integration.

Most actions forward the upstream JSON body wholesale on ``result``;
the few that aggregate paged data (search_*, list_*) hoist the
collection / pagination fields up to the top level for ergonomic
access. ``upsert_contact`` additionally tracks whether the operation
was an update vs a fresh create via ``action_type``.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddTagToContactOutput",
    "CreateNoteOutput",
    "GetContactOutput",
    "GetConversationOutput",
    "ListAdminsOutput",
    "ListConversationsOutput",
    "ListTagsOutput",
    "ReplyToConversationOutput",
    "SearchContactsOutput",
    "SearchConversationsOutput",
    "SendIncomingMessageOutput",
    "SendMessageToContactOutput",
    "UpsertContactOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class GetContactOutput(_Base):
    result: dict[str, Any] | None = None


class SearchContactsOutput(_Base):
    contacts: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    pages: dict[str, Any] | None = None


class UpsertContactOutput(_Base):
    # "created" or "updated" — tracks the side-call branch we took.
    action_type: str | None = None
    contact: dict[str, Any] | None = None


class CreateNoteOutput(_Base):
    result: dict[str, Any] | None = None


class AddTagToContactOutput(_Base):
    result: dict[str, Any] | None = None


class ListTagsOutput(_Base):
    result: dict[str, Any] | None = None


class ListAdminsOutput(_Base):
    result: dict[str, Any] | None = None


class GetConversationOutput(_Base):
    result: dict[str, Any] | None = None


class ListConversationsOutput(_Base):
    conversations: list[dict[str, Any]] = Field(default_factory=list)
    pages: dict[str, Any] | None = None


class SearchConversationsOutput(_Base):
    conversations: list[dict[str, Any]] = Field(default_factory=list)
    total_count: int = 0
    pages: dict[str, Any] | None = None


class SendIncomingMessageOutput(_Base):
    result: dict[str, Any] | None = None


class SendMessageToContactOutput(_Base):
    result: dict[str, Any] | None = None


class ReplyToConversationOutput(_Base):
    result: dict[str, Any] | None = None
