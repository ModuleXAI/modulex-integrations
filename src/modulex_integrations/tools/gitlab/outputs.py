"""Pydantic response models for the gitlab integration's @tool functions."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "BranchCommit",
    "BranchSummary",
    "CommitSummary",
    "CreateBranchOutput",
    "CreateEpicOutput",
    "CreateIssueOutput",
    "EpicSummary",
    "GetIssueOutput",
    "GetRepoBranchOutput",
    "GroupSummary",
    "IssueSummary",
    "ListCommitsOutput",
    "ListGroupsOutput",
    "ListProjectMembersOutput",
    "ListRepoBranchesOutput",
    "MemberSummary",
    "SearchIssuesOutput",
    "UpdateEpicOutput",
    "UpdateIssueOutput",
]


class _Base(BaseModel):
    """Shared config for every output model in this integration."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models -----------------------------------------------


class BranchCommit(_Base):
    id: str | None = None
    short_id: str | None = None
    title: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    created_at: str | None = None
    message: str | None = None


class BranchSummary(_Base):
    name: str | None = None
    commit: BranchCommit | None = None
    merged: bool | None = None
    protected: bool | None = None
    developers_can_push: bool | None = None
    developers_can_merge: bool | None = None
    can_push: bool | None = None
    web_url: str | None = None


class EpicSummary(_Base):
    id: int | None = None
    iid: int | None = None
    group_id: int | None = None
    title: str | None = None
    description: str | None = None
    state: str | None = None
    confidential: bool | None = None
    web_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    labels: list[str] = Field(default_factory=list)


class IssueSummary(_Base):
    id: int | None = None
    iid: int | None = None
    project_id: int | None = None
    title: str | None = None
    description: str | None = None
    state: str | None = None
    web_url: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)


class CommitSummary(_Base):
    id: str | None = None
    short_id: str | None = None
    title: str | None = None
    author_name: str | None = None
    author_email: str | None = None
    authored_date: str | None = None
    committed_date: str | None = None
    message: str | None = None
    web_url: str | None = None


class GroupSummary(_Base):
    id: int | None = None
    name: str | None = None
    path: str | None = None
    description: str | None = None
    visibility: str | None = None
    web_url: str | None = None
    full_name: str | None = None
    full_path: str | None = None


class MemberSummary(_Base):
    id: int | None = None
    username: str | None = None
    name: str | None = None
    state: str | None = None
    access_level: int | None = None
    web_url: str | None = None


# --- Per-action output models ----------------------------------------------


class CreateBranchOutput(_Base):
    success: bool
    branch: BranchSummary | None = None


class CreateEpicOutput(_Base):
    success: bool
    epic: EpicSummary | None = None


class CreateIssueOutput(_Base):
    success: bool
    issue: IssueSummary | None = None


class GetIssueOutput(_Base):
    success: bool
    issue: IssueSummary | None = None


class GetRepoBranchOutput(_Base):
    success: bool
    branch: BranchSummary | None = None


class ListCommitsOutput(_Base):
    success: bool
    commits: list[CommitSummary] = Field(default_factory=list)


class ListGroupsOutput(_Base):
    success: bool
    groups: list[GroupSummary] = Field(default_factory=list)


class ListProjectMembersOutput(_Base):
    success: bool
    members: list[MemberSummary] = Field(default_factory=list)


class ListRepoBranchesOutput(_Base):
    success: bool
    branches: list[BranchSummary] = Field(default_factory=list)


class SearchIssuesOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)


class UpdateEpicOutput(_Base):
    success: bool
    epic: EpicSummary | None = None


class UpdateIssueOutput(_Base):
    success: bool
    issue: IssueSummary | None = None
