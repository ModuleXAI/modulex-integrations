"""Pydantic response models for the GitHub integration's @tool functions.

Each ``@tool`` function in ``tools.py`` carries one of these models as
its return-type annotation. The modulex runtime derives the LLM-facing
output JSONSchema from each model via ``Model.model_json_schema()``.

Field types are intentionally permissive (``X | None``): the GitHub API
sometimes omits fields, and the legacy modulex code passed values
through with ``.get()``. Preserving that behavior keeps the migration
behavior-equivalent.
"""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "Branch",
    "CommitCreated",
    "CreateBranchOutput",
    "CreateCommitOutput",
    "CreateIssueOutput",
    "CreatePullRequestOutput",
    "CreateRepositoryOutput",
    "DeleteRepositoryOutput",
    "FileContent",
    "GetFileContentOutput",
    "GetIssueOutput",
    "GetPullRequestOutput",
    "GetRepositoryOutput",
    "IssueCreated",
    "IssueSummary",
    "IssueUpdated",
    "ListIssuesOutput",
    "ListPullRequestsOutput",
    "ListRepositoriesOutput",
    "MergePullRequestOutput",
    "PullRequestCreated",
    "PullRequestDetailed",
    "PullRequestSummary",
    "RepositoryCreated",
    "RepositoryDetailed",
    "RepositorySummary",
    "SearchCodeItem",
    "SearchCodeOutput",
    "UpdateIssueOutput",
]


class _Base(BaseModel):
    """Shared config for every output model."""

    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class RepositorySummary(_Base):
    """One row of ``list_repositories``."""

    id: int | None = None
    name: str | None = None
    full_name: str | None = None
    description: str | None = None
    private: bool | None = None
    url: str | None = None
    clone_url: str | None = None
    ssh_url: str | None = None
    language: str | None = None
    stars: int | None = None
    forks: int | None = None
    open_issues: int | None = None
    default_branch: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class RepositoryCreated(_Base):
    """Repository representation from ``create_repository``."""

    id: int | None = None
    name: str | None = None
    full_name: str | None = None
    owner: str | None = None
    url: str | None = None
    clone_url: str | None = None
    private: bool | None = None
    default_branch: str | None = None


class RepositoryDetailed(_Base):
    """Repository representation from ``get_repository``."""

    id: int | None = None
    name: str | None = None
    full_name: str | None = None
    description: str | None = None
    private: bool | None = None
    url: str | None = None
    clone_url: str | None = None
    ssh_url: str | None = None
    language: str | None = None
    stars: int | None = None
    forks: int | None = None
    watchers: int | None = None
    open_issues: int | None = None
    default_branch: str | None = None
    topics: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    pushed_at: str | None = None


class IssueSummary(_Base):
    """Issue row in ``list_issues`` / single fetch in ``get_issue``."""

    number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    url: str | None = None
    user: str | None = None
    labels: list[str] = Field(default_factory=list)
    assignees: list[str] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None
    closed_at: str | None = None
    comments: int | None = None


class IssueCreated(_Base):
    """Issue representation from ``create_issue``."""

    number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    url: str | None = None
    created_at: str | None = None


class IssueUpdated(_Base):
    """Issue representation from ``update_issue``."""

    number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    url: str | None = None
    updated_at: str | None = None


class PullRequestSummary(_Base):
    """PR row in ``list_pull_requests``."""

    number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    url: str | None = None
    user: str | None = None
    head: str | None = None
    base: str | None = None
    draft: bool | None = None
    mergeable: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    merged_at: str | None = None
    closed_at: str | None = None


class PullRequestCreated(_Base):
    """PR representation from ``create_pull_request``."""

    number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    url: str | None = None
    draft: bool | None = None
    head: str | None = None
    base: str | None = None
    created_at: str | None = None


class PullRequestDetailed(_Base):
    """PR representation from ``get_pull_request``."""

    number: int | None = None
    title: str | None = None
    body: str | None = None
    state: str | None = None
    url: str | None = None
    user: str | None = None
    head: str | None = None
    base: str | None = None
    draft: bool | None = None
    mergeable: bool | None = None
    merged: bool | None = None
    created_at: str | None = None
    updated_at: str | None = None
    merged_at: str | None = None
    closed_at: str | None = None
    commits: int | None = None
    additions: int | None = None
    deletions: int | None = None
    changed_files: int | None = None


class Branch(_Base):
    """Branch returned by ``create_branch``."""

    name: str | None = None
    ref: str | None = None
    sha: str | None = None


class FileContent(_Base):
    """File returned by ``get_file_content`` (content is base64-decoded UTF-8)."""

    name: str | None = None
    path: str | None = None
    size: int | None = None
    content: str | None = None
    sha: str | None = None
    download_url: str | None = None


class CommitCreated(_Base):
    """Commit returned by ``create_commit``."""

    sha: str | None = None
    message: str | None = None
    branch: str | None = None


class SearchCodeItem(_Base):
    """One result row of ``search_code``."""

    name: str | None = None
    path: str | None = None
    repository: str | None = None
    url: str | None = None
    sha: str | None = None


# --- Per-action output models ----------------------------------------------


class ListRepositoriesOutput(_Base):
    success: bool
    repositories: list[RepositorySummary] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 30


class CreateRepositoryOutput(_Base):
    success: bool
    repository: RepositoryCreated


class DeleteRepositoryOutput(_Base):
    success: bool
    message: str


class GetRepositoryOutput(_Base):
    success: bool
    repository: RepositoryDetailed


class ListIssuesOutput(_Base):
    success: bool
    issues: list[IssueSummary] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 30


class CreateIssueOutput(_Base):
    success: bool
    issue: IssueCreated


class GetIssueOutput(_Base):
    success: bool
    issue: IssueSummary


class UpdateIssueOutput(_Base):
    success: bool
    issue: IssueUpdated


class ListPullRequestsOutput(_Base):
    success: bool
    pull_requests: list[PullRequestSummary] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    per_page: int = 30


class CreatePullRequestOutput(_Base):
    success: bool
    pull_request: PullRequestCreated


class GetPullRequestOutput(_Base):
    success: bool
    pull_request: PullRequestDetailed


class MergePullRequestOutput(_Base):
    success: bool
    merged: bool | None = None
    message: str | None = None
    sha: str | None = None


class CreateBranchOutput(_Base):
    success: bool
    branch: Branch


class GetFileContentOutput(_Base):
    success: bool
    file: FileContent


class CreateCommitOutput(_Base):
    success: bool
    commit: CommitCreated


class SearchCodeOutput(_Base):
    success: bool
    total_count: int = 0
    items: list[SearchCodeItem] = Field(default_factory=list)
    page: int = 1
    per_page: int = 30
