"""Pydantic response models for the Gmail integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddLabelOutput",
    "ArchiveMessageOutput",
    "CreateDraftOutput",
    "DeleteMessageOutput",
    "GmailMessageSummary",
    "ListLabelsOutput",
    "ListMessagesOutput",
    "MarkAsReadOutput",
    "MarkAsUnreadOutput",
    "ReadMessageOutput",
    "RemoveLabelOutput",
    "SearchMessagesOutput",
    "SendMessageOutput",
    "UnarchiveMessageOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class _MessageStub(_Base):
    """Common shape for mark/archive/label-modify endpoints."""

    id: str | None = None
    thread_id: str | None = None
    label_ids: list[str] = Field(default_factory=list)
    message: str | None = None


class SendMessageOutput(_Base):
    id: str | None = None
    thread_id: str | None = None
    label_ids: list[str] = Field(default_factory=list)


class ReadMessageOutput(_Base):
    id: str | None = None
    thread_id: str | None = None
    label_ids: list[str] = Field(default_factory=list)
    snippet: str | None = None
    subject: str | None = None
    from_address: str | None = None
    to: str | None = None
    cc: str | None = None
    date: str | None = None
    body: str | None = None
    internal_date: str | None = None
    size_estimate: int | None = None


class GmailMessageSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str | None = None
    thread_id: str | None = None
    snippet: str | None = None
    subject: str | None = None
    from_address: str | None = None
    date: str | None = None
    label_ids: list[str] = Field(default_factory=list)


class SearchMessagesOutput(_Base):
    messages: list[GmailMessageSummary] = Field(default_factory=list)
    total: int = 0
    result_size_estimate: int | None = None
    next_page_token: str | None = None


class ListMessagesOutput(_Base):
    messages: list[GmailMessageSummary] = Field(default_factory=list)
    total: int = 0
    next_page_token: str | None = None


class CreateDraftOutput(_Base):
    draft_id: str | None = None
    message_id: str | None = None
    thread_id: str | None = None


class MarkAsReadOutput(_MessageStub):
    pass


class MarkAsUnreadOutput(_MessageStub):
    pass


class ArchiveMessageOutput(_MessageStub):
    pass


class UnarchiveMessageOutput(_MessageStub):
    pass


class DeleteMessageOutput(_Base):
    id: str | None = None
    thread_id: str | None = None
    message: str | None = None


class AddLabelOutput(_MessageStub):
    added_labels: list[str] = Field(default_factory=list)


class RemoveLabelOutput(_MessageStub):
    removed_labels: list[str] = Field(default_factory=list)


class ListLabelsOutput(_Base):
    labels: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
