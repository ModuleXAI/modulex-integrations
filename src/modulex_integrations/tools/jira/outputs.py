"""Pydantic response models for the jira integration's @tool functions."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddAttachmentToIssueOutput",
    "AddCommentToIssueOutput",
    "AddMultipleAttachmentsToIssueOutput",
    "AddWatcherToIssueOutput",
    "AssignIssueOutput",
    "BoardSummary",
    "CheckIssuesAgainstJqlOutput",
    "CloudSite",
    "CommentSummary",
    "CountIssuesUsingJqlOutput",
    "CreateCustomFieldOptionsContextOutput",
    "CreateFutureSprintOutput",
    "CreateIssueOutput",
    "CreateVersionOutput",
    "DeleteProjectOutput",
    "EpicSummary",
    "GetAllProjectsOutput",
    "GetBoardOutput",
    "GetCloudIdOutput",
    "GetCurrentUserOutput",
    "GetIssueOutput",
    "GetIssuePickerSuggestionsOutput",
    "GetIssueTypesOutput",
    "GetSprintOutput",
    "GetTaskOutput",
    "GetTransitionsOutput",
    "GetUserOutput",
    "GetUsersOutput",
    "IssueSummary",
    "IssueTypeSummary",
    "JqlMatchResult",
    "ListBoardIssuesOutput",
    "ListBoardsOutput",
    "ListEpicIssuesOutput",
    "ListEpicsOutput",
    "ListIssueCommentsOutput",
    "ListLabelsOptionsOutput",
    "ListSprintIssuesOutput",
    "ListSprintsOutput",
    "MoveIssuesToSprintOutput",
    "ProjectSummary",
    "SearchIssuesWithJqlOutput",
    "SearchIssuesWithJqlPostOutput",
    "SprintSummary",
    "SuggestionSection",
    "TransitionIssueOutput",
    "TransitionSummary",
    "UpdateCommentOutput",
    "UpdateIssueOutput",
    "UserSummary",
    "VersionSummary",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class CloudSite(_Base):
    id: str | None = None
    url: str | None = None
    name: str | None = None
    scopes: list[str] = Field(default_factory=list)
    avatar_url: str | None = None


class UserSummary(_Base):
    account_id: str | None = None
    display_name: str | None = None
    email_address: str | None = None
    active: bool | None = None
    avatar_url: str | None = None
    account_type: str | None = None


class IssueSummary(_Base):
    id: str | None = None
    key: str | None = None
    self_url: str | None = None
    summary: str | None = None
    status: str | None = None
    issue_type: str | None = None
    priority: str | None = None
    assignee: str | None = None
    reporter: str | None = None
    created: str | None = None
    updated: str | None = None
    fields: dict[str, Any] | None = None


class CommentSummary(_Base):
    id: str | None = None
    self_url: str | None = None
    body: Any | None = None
    author: str | None = None
    created: str | None = None
    updated: str | None = None


class BoardSummary(_Base):
    id: int | None = None
    name: str | None = None
    board_type: str | None = None
    self_url: str | None = None


class SprintSummary(_Base):
    id: int | None = None
    name: str | None = None
    state: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    complete_date: str | None = None
    goal: str | None = None
    self_url: str | None = None


class EpicSummary(_Base):
    id: int | None = None
    key: str | None = None
    name: str | None = None
    summary: str | None = None
    done: bool | None = None
    self_url: str | None = None


class ProjectSummary(_Base):
    id: str | None = None
    key: str | None = None
    name: str | None = None
    project_type_key: str | None = None
    self_url: str | None = None


class IssueTypeSummary(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    subtask: bool | None = None
    self_url: str | None = None


class TransitionSummary(_Base):
    id: str | None = None
    name: str | None = None
    to_status: str | None = None
    has_screen: bool | None = None


class VersionSummary(_Base):
    id: str | None = None
    name: str | None = None
    description: str | None = None
    archived: bool | None = None
    released: bool | None = None
    start_date: str | None = None
    release_date: str | None = None
    self_url: str | None = None


class JqlMatchResult(_Base):
    issue_id: str | None = None
    matched_jqls: list[str] = Field(default_factory=list)


class SuggestionSection(_Base):
    label: str | None = None
    issues: list[IssueSummary] = Field(default_factory=list)


# --- Per-action output models ---------------------------------------------


class AddAttachmentToIssueOutput(_Base):
    success: bool
    id: str | None = None
    filename: str | None = None
    mime_type: str | None = None
    size: int | None = None
    self_url: str | None = None


class AddCommentToIssueOutput(_Base):
    success: bool
    comment: CommentSummary | None = None


class AddMultipleAttachmentsToIssueOutput(_Base):
    success: bool
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class AddWatcherToIssueOutput(_Base):
    success: bool


class AssignIssueOutput(_Base):
    success: bool


class CheckIssuesAgainstJqlOutput(_Base):
    success: bool
    matches: list[JqlMatchResult] = Field(default_factory=list)


class CountIssuesUsingJqlOutput(_Base):
    success: bool
    count: int | None = None


class CreateCustomFieldOptionsContextOutput(_Base):
    success: bool
    options: list[dict[str, Any]] = Field(default_factory=list)


class CreateFutureSprintOutput(_Base):
    success: bool
    sprint: SprintSummary | None = None


class CreateIssueOutput(_Base):
    success: bool
    id: str | None = None
    key: str | None = None
    self_url: str | None = None


class CreateVersionOutput(_Base):
    success: bool
    version: VersionSummary | None = None


class DeleteProjectOutput(_Base):
    success: bool


class GetAllProjectsOutput(_Base):
    success: bool
    projects: list[ProjectSummary] = Field(default_factory=list)
    total: int | None = None


class GetBoardOutput(_Base):
    success: bool
    board: BoardSummary | None = None


class GetCloudIdOutput(_Base):
    success: bool
    sites: list[CloudSite] = Field(default_factory=list)


class GetCurrentUserOutput(_Base):
    success: bool
    user: UserSummary | None = None


class GetIssueOutput(_Base):
    success: bool
    issue: IssueSummary | None = None


class GetIssuePickerSuggestionsOutput(_Base):
    success: bool
    sections: list[SuggestionSection] = Field(default_factory=list)


class GetIssueTypesOutput(_Base):
    success: bool
    issue_types: list[IssueTypeSummary] = Field(default_factory=list)


class GetSprintOutput(_Base):
    success: bool
    sprint: SprintSummary | None = None


class GetTaskOutput(_Base):
    success: bool
    status: str | None = None
    progress: int | None = None
    result: str | None = None
    task_id: str | None = None


class GetTransitionsOutput(_Base):
    success: bool
    transitions: list[TransitionSummary] = Field(default_factory=list)


class GetUserOutput(_Base):
    success: bool
    user: UserSummary | None = None


class GetUsersOutput(_Base):
    success: bool
    users: list[UserSummary] = Field(default_factory=list)


class ListBoardIssuesOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class ListBoardsOutput(_Base):
    success: bool
    boards: list[BoardSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class ListEpicIssuesOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class ListEpicsOutput(_Base):
    success: bool
    epics: list[EpicSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class ListIssueCommentsOutput(_Base):
    success: bool
    comments: list[CommentSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class ListLabelsOptionsOutput(_Base):
    success: bool
    labels: list[str] = Field(default_factory=list)
    total: int | None = None


class ListSprintIssuesOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class ListSprintsOutput(_Base):
    success: bool
    sprints: list[SprintSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class MoveIssuesToSprintOutput(_Base):
    success: bool


class SearchIssuesWithJqlOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)
    total: int | None = None
    start_at: int | None = None
    max_results: int | None = None


class SearchIssuesWithJqlPostOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)
    total: int | None = None
    next_page_token: str | None = None


class TransitionIssueOutput(_Base):
    success: bool


class UpdateCommentOutput(_Base):
    success: bool
    comment: CommentSummary | None = None


class UpdateIssueOutput(_Base):
    success: bool
