"""Pydantic response models for the Zendesk integration."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddTicketTagsOutput",
    "CreateTicketOutput",
    "DeleteTicketOutput",
    "GetArticleOutput",
    "GetMacroOutput",
    "GetTicketOutput",
    "GetUserOutput",
    "ListArticlesOutput",
    "ListLocalesOutput",
    "ListMacrosOutput",
    "ListTicketCommentsOutput",
    "ListTicketsOutput",
    "RemoveTicketTagsOutput",
    "SearchTicketsOutput",
    "SetCustomFieldsOutput",
    "SetTicketTagsOutput",
    "TicketSummary",
    "UpdateTicketOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")
    success: bool
    error: str | None = None


class TicketSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: int | None = None
    subject: str | None = None
    status: str | None = None
    priority: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    ticket: dict[str, Any] | None = None


class CreateTicketOutput(TicketSummary, _Base):
    pass


class UpdateTicketOutput(TicketSummary, _Base):
    pass


class DeleteTicketOutput(_Base):
    id: int | None = None
    deleted: bool = False


class GetTicketOutput(_Base):
    result: dict[str, Any] | None = None


class ListTicketsOutput(_Base):
    tickets: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    next_page: str | None = None
    previous_page: str | None = None


class SearchTicketsOutput(_Base):
    results: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    next_page: str | None = None
    previous_page: str | None = None


class _TagsOutput(_Base):
    ticket_id: int | None = None
    tags: list[str] = Field(default_factory=list)


class AddTicketTagsOutput(_TagsOutput):
    added_count: int = 0


class SetTicketTagsOutput(_TagsOutput):
    pass


class RemoveTicketTagsOutput(_TagsOutput):
    removed_count: int = 0


class ListTicketCommentsOutput(_Base):
    ticket_id: int | None = None
    comments: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    next_page: str | None = None


class SetCustomFieldsOutput(_Base):
    id: int | None = None
    custom_fields: list[dict[str, Any]] = Field(default_factory=list)


class GetUserOutput(_Base):
    result: dict[str, Any] | None = None


class ListLocalesOutput(_Base):
    locales: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0


class ListMacrosOutput(_Base):
    macros: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    next_page: str | None = None


class GetMacroOutput(_Base):
    result: dict[str, Any] | None = None


class ListArticlesOutput(_Base):
    articles: list[dict[str, Any]] = Field(default_factory=list)
    count: int = 0
    next_page: str | None = None


class GetArticleOutput(_Base):
    result: dict[str, Any] | None = None
