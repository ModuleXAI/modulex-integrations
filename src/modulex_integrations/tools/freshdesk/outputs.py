"""Pydantic response models for the freshdesk integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddNoteToTicketOutput",
    "AddTicketTagsOutput",
    "AssignTicketToAgentOutput",
    "AssignTicketToGroupOutput",
    "CloseTicketOutput",
    "CreateAgentOutput",
    "CreateCompanyOutput",
    "CreateContactOutput",
    "CreateMessageForThreadOutput",
    "CreateReplyOutput",
    "CreateSolutionArticleOutput",
    "CreateThreadOutput",
    "CreateTicketFieldOutput",
    "CreateTicketOutput",
    "DeleteSolutionArticleOutput",
    "ForwardTicketOutput",
    "GetAgentOutput",
    "GetCannedResponseOutput",
    "GetContactOutput",
    "GetFolderCannedResponsesOutput",
    "GetSolutionArticleOutput",
    "GetTicketOutput",
    "ListAgentsOutput",
    "ListAllFoldersOutput",
    "ListAllTicketsOutput",
    "ListCategoryFoldersOutput",
    "ListCompaniesOutput",
    "ListEmailConfigsOutput",
    "ListFolderArticlesOutput",
    "ListFolderCannedResponsesOutput",
    "ListRolesOutput",
    "ListSolutionCategoriesOutput",
    "ListTicketConversationsOutput",
    "ListTicketFieldsOutput",
    "RemoveTicketTagsOutput",
    "ReplyToForwardOutput",
    "SearchSolutionArticleOutput",
    "SetTicketPriorityOutput",
    "SetTicketStatusOutput",
    "SetTicketTagsOutput",
    "UpdateAgentOutput",
    "UpdateContactOutput",
    "UpdateSolutionArticleOutput",
    "UpdateTicketFieldOutput",
    "UpdateTicketOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


class CreateTicketOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetTicketOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateTicketOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListAllTicketsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class CloseTicketOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddNoteToTicketOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AddTicketTagsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class RemoveTicketTagsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SetTicketTagsOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SetTicketPriorityOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class SetTicketStatusOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AssignTicketToAgentOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class AssignTicketToGroupOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateContactOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetContactOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateContactOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateCompanyOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateAgentOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateAgentOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetAgentOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListAgentsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class CreateReplyOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ForwardTicketOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ReplyToForwardOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateThreadOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateMessageForThreadOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class ListTicketConversationsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListTicketFieldsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class CreateTicketFieldOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateTicketFieldOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class CreateSolutionArticleOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetSolutionArticleOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class UpdateSolutionArticleOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class DeleteSolutionArticleOutput(_Base):
    success: bool
    error: str | None = None


class SearchSolutionArticleOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListSolutionCategoriesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListCategoryFoldersOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListFolderArticlesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListAllFoldersOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListFolderCannedResponsesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class GetCannedResponseOutput(_Base):
    success: bool
    error: str | None = None
    data: dict[str, Any] | None = None


class GetFolderCannedResponsesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListCompaniesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListEmailConfigsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)


class ListRolesOutput(_Base):
    success: bool
    error: str | None = None
    items: list[dict[str, Any]] = Field(default_factory=list)
