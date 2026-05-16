"""GitHub LangChain ``@tool`` functions.

Sixteen async tools wrapping the GitHub REST API. Each takes
``auth_type`` and ``auth_data`` as the first two parameters; the modulex
``ToolExecutor`` injects them at call time so the LLM never sees them.

Every function returns a typed pydantic response model defined in
``outputs.py`` — the runtime derives JSONSchema for downstream consumers
from those models.

HTTP errors raise via ``response.raise_for_status()``; pydantic models
describe success cases only. This mirrors the legacy modulex behavior.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.github.outputs import (
    Branch,
    CommitCreated,
    CreateBranchOutput,
    CreateCommitOutput,
    CreateIssueOutput,
    CreatePullRequestOutput,
    CreateRepositoryOutput,
    DeleteRepositoryOutput,
    FileContent,
    GetFileContentOutput,
    GetIssueOutput,
    GetPullRequestOutput,
    GetRepositoryOutput,
    IssueCreated,
    IssueSummary,
    IssueUpdated,
    ListIssuesOutput,
    ListPullRequestsOutput,
    ListRepositoriesOutput,
    MergePullRequestOutput,
    PullRequestCreated,
    PullRequestDetailed,
    PullRequestSummary,
    RepositoryCreated,
    RepositoryDetailed,
    RepositorySummary,
    SearchCodeItem,
    SearchCodeOutput,
    UpdateIssueOutput,
)

__all__ = [
    "create_branch",
    "create_commit",
    "create_issue",
    "create_pull_request",
    "create_repository",
    "delete_repository",
    "get_file_content",
    "get_issue",
    "get_pull_request",
    "get_repository",
    "list_issues",
    "list_pull_requests",
    "list_repositories",
    "merge_pull_request",
    "search_code",
    "update_issue",
]


# --- Auth helpers ----------------------------------------------------------


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    """Build GitHub API headers for the given credential.

    Supports:
    - ``oauth2``: reads ``access_token`` from auth_data
    - ``bearer_token``: reads ``token`` from auth_data
    """
    headers: dict[str, str] = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    elif auth_type == "bearer_token":
        token = auth_data.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
    return headers


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListRepositoriesInput(BaseModel):
    auth_type: str = Field(description="Authentication type (oauth2, bearer_token)")
    auth_data: dict[str, Any] = Field(description="Authentication data containing tokens")
    visibility: str = Field(default="all", description="Filter by visibility: all, public, private")
    affiliation: str = Field(
        default="owner,collaborator,organization_member",
        description="Comma-separated list of affiliations",
    )
    sort: str = Field(
        default="full_name",
        description="Sort by: created, updated, pushed, full_name",
    )
    direction: str = Field(default="asc", description="Sort direction: asc or desc")
    per_page: int = Field(default=30, description="Results per page (max 100)")
    page: int = Field(default=1, description="Page number")


class CreateRepositoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    name: str = Field(description="Repository name")
    description: str | None = Field(default=None, description="Repository description")
    private: bool = Field(default=False, description="Whether the repository is private")
    auto_init: bool = Field(default=False, description="Initialize with README")


class DeleteRepositoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner (username or organization)")
    repo: str = Field(description="Repository name to delete")


class GetRepositoryInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")


class ListIssuesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    state: str = Field(default="open", description="Issue state: open, closed, all")
    labels: str | None = Field(default=None, description="Comma-separated list of label names")
    sort: str = Field(default="created", description="Sort by: created, updated, comments")
    direction: str = Field(default="desc", description="Sort direction: asc, desc")
    per_page: int = Field(default=30, description="Results per page")
    page: int = Field(default=1, description="Page number")


class CreateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    title: str = Field(description="Issue title")
    body: str | None = Field(default=None, description="Issue body/description")
    labels: list[str] | None = Field(default=None, description="List of label names")
    assignees: list[str] | None = Field(default=None, description="List of usernames to assign")


class GetIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    issue_number: int = Field(description="Issue number")


class UpdateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    issue_number: int = Field(description="Issue number")
    title: str | None = Field(default=None, description="New title")
    body: str | None = Field(default=None, description="New body")
    state: str | None = Field(default=None, description="New state: open, closed")
    labels: list[str] | None = Field(default=None, description="New labels list")
    assignees: list[str] | None = Field(default=None, description="New assignees list")


class ListPullRequestsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    state: str = Field(default="open", description="PR state: open, closed, all")
    sort: str = Field(
        default="created",
        description="Sort by: created, updated, popularity, long-running",
    )
    direction: str = Field(default="desc", description="Sort direction: asc, desc")
    per_page: int = Field(default=30, description="Results per page")
    page: int = Field(default=1, description="Page number")


class CreatePullRequestInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    title: str = Field(description="PR title")
    head: str = Field(description="Name of the branch where changes are implemented")
    base: str = Field(description="Name of the branch you want changes pulled into")
    body: str | None = Field(default=None, description="PR description")
    draft: bool = Field(default=False, description="Create as draft PR")


class GetPullRequestInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    pull_number: int = Field(description="Pull request number")


class MergePullRequestInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    pull_number: int = Field(description="Pull request number")
    commit_title: str | None = Field(default=None, description="Title for merge commit")
    commit_message: str | None = Field(default=None, description="Message for merge commit")
    merge_method: str = Field(default="merge", description="Merge method: merge, squash, rebase")


class CreateBranchInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    branch_name: str = Field(description="Name for the new branch")
    from_branch: str = Field(default="main", description="Base branch to create from")


class GetFileContentInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    path: str = Field(description="Path to the file")
    ref: str | None = Field(default=None, description="Branch, tag, or commit SHA")


class CreateCommitInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    owner: str = Field(description="Repository owner")
    repo: str = Field(description="Repository name")
    branch: str = Field(description="Branch to commit to")
    message: str = Field(description="Commit message")
    files: list[dict[str, str]] = Field(
        description="List of file changes: [{'path': 'file.txt', 'content': '...'}]"
    )


class SearchCodeInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    query: str = Field(description="Search query (supports qualifiers)")
    sort: str | None = Field(default=None, description="Sort by (indexed only)")
    order: str = Field(default="desc", description="Sort order: asc, desc")
    per_page: int = Field(default=30, description="Results per page")
    page: int = Field(default=1, description="Page number")


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListRepositoriesInput)
@serialize_pydantic_return
async def list_repositories(
    auth_type: str,
    auth_data: dict[str, Any],
    visibility: str = "all",
    affiliation: str = "owner,collaborator,organization_member",
    sort: str = "full_name",
    direction: str = "asc",
    per_page: int = 30,
    page: int = 1,
) -> ListRepositoriesOutput:
    """List repositories for the authenticated user."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "visibility": visibility,
        "affiliation": affiliation,
        "sort": sort,
        "direction": direction,
        "per_page": per_page,
        "page": page,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user/repos", headers=headers, params=params
        )
        response.raise_for_status()
        repos = response.json()
    return ListRepositoriesOutput(
        success=True,
        repositories=[
            RepositorySummary(
                id=r.get("id"),
                name=r.get("name"),
                full_name=r.get("full_name"),
                description=r.get("description"),
                private=r.get("private"),
                url=r.get("html_url"),
                clone_url=r.get("clone_url"),
                ssh_url=r.get("ssh_url"),
                language=r.get("language"),
                stars=r.get("stargazers_count"),
                forks=r.get("forks_count"),
                open_issues=r.get("open_issues_count"),
                default_branch=r.get("default_branch"),
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
            )
            for r in repos
        ],
        total=len(repos),
        page=page,
        per_page=per_page,
    )


@tool(args_schema=CreateRepositoryInput)
@serialize_pydantic_return
async def create_repository(
    auth_type: str,
    auth_data: dict[str, Any],
    name: str,
    description: str | None = None,
    private: bool = False,
    auto_init: bool = False,
) -> CreateRepositoryOutput:
    """Create a new repository for the authenticated user."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"name": name, "private": private, "auto_init": auto_init}
    if description:
        payload["description"] = description
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.github.com/user/repos", headers=headers, json=payload
        )
        response.raise_for_status()
        repo = response.json()
    full_name: str = repo.get("full_name", "") or ""
    owner = full_name.split("/")[0] if "/" in full_name else ""
    return CreateRepositoryOutput(
        success=True,
        repository=RepositoryCreated(
            id=repo.get("id"),
            name=repo.get("name"),
            full_name=full_name or None,
            owner=owner or None,
            url=repo.get("html_url"),
            clone_url=repo.get("clone_url"),
            private=repo.get("private"),
            default_branch=repo.get("default_branch", "main"),
        ),
    )


@tool(args_schema=DeleteRepositoryInput)
@serialize_pydantic_return
async def delete_repository(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
) -> DeleteRepositoryOutput:
    """Delete a repository (irreversible; requires delete_repo scope)."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"https://api.github.com/repos/{owner}/{repo}", headers=headers
        )
        response.raise_for_status()
    return DeleteRepositoryOutput(
        success=True,
        message=f"Repository {owner}/{repo} has been deleted",
    )


@tool(args_schema=GetRepositoryInput)
@serialize_pydantic_return
async def get_repository(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
) -> GetRepositoryOutput:
    """Get detailed information about a repository."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}", headers=headers
        )
        response.raise_for_status()
        r = response.json()
    return GetRepositoryOutput(
        success=True,
        repository=RepositoryDetailed(
            id=r.get("id"),
            name=r.get("name"),
            full_name=r.get("full_name"),
            description=r.get("description"),
            private=r.get("private"),
            url=r.get("html_url"),
            clone_url=r.get("clone_url"),
            ssh_url=r.get("ssh_url"),
            language=r.get("language"),
            stars=r.get("stargazers_count"),
            forks=r.get("forks_count"),
            watchers=r.get("watchers_count"),
            open_issues=r.get("open_issues_count"),
            default_branch=r.get("default_branch"),
            topics=r.get("topics") or [],
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
            pushed_at=r.get("pushed_at"),
        ),
    )


@tool(args_schema=ListIssuesInput)
@serialize_pydantic_return
async def list_issues(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    state: str = "open",
    labels: str | None = None,
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 30,
    page: int = 1,
) -> ListIssuesOutput:
    """List issues in a repository."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "per_page": per_page,
        "page": page,
    }
    if labels:
        params["labels"] = labels
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        issues = response.json()
    return ListIssuesOutput(
        success=True,
        issues=[
            IssueSummary(
                number=i.get("number"),
                title=i.get("title"),
                body=i.get("body"),
                state=i.get("state"),
                url=i.get("html_url"),
                user=(i.get("user") or {}).get("login"),
                labels=[lbl.get("name") for lbl in i.get("labels") or [] if lbl.get("name")],
                assignees=[a.get("login") for a in i.get("assignees") or [] if a.get("login")],
                created_at=i.get("created_at"),
                updated_at=i.get("updated_at"),
                closed_at=i.get("closed_at"),
                comments=i.get("comments"),
            )
            for i in issues
        ],
        total=len(issues),
        page=page,
        per_page=per_page,
    )


@tool(args_schema=CreateIssueInput)
@serialize_pydantic_return
async def create_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    title: str,
    body: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
) -> CreateIssueOutput:
    """Create an issue in a repository."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"title": title}
    if body:
        payload["body"] = body
    if labels:
        payload["labels"] = labels
    if assignees:
        payload["assignees"] = assignees
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        i = response.json()
    return CreateIssueOutput(
        success=True,
        issue=IssueCreated(
            number=i.get("number"),
            title=i.get("title"),
            body=i.get("body"),
            state=i.get("state"),
            url=i.get("html_url"),
            created_at=i.get("created_at"),
        ),
    )


@tool(args_schema=GetIssueInput)
@serialize_pydantic_return
async def get_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    issue_number: int,
) -> GetIssueOutput:
    """Get a specific issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
            headers=headers,
        )
        response.raise_for_status()
        i = response.json()
    return GetIssueOutput(
        success=True,
        issue=IssueSummary(
            number=i.get("number"),
            title=i.get("title"),
            body=i.get("body"),
            state=i.get("state"),
            url=i.get("html_url"),
            user=(i.get("user") or {}).get("login"),
            labels=[lbl.get("name") for lbl in i.get("labels") or [] if lbl.get("name")],
            assignees=[a.get("login") for a in i.get("assignees") or [] if a.get("login")],
            created_at=i.get("created_at"),
            updated_at=i.get("updated_at"),
            closed_at=i.get("closed_at"),
            comments=i.get("comments"),
        ),
    )


@tool(args_schema=UpdateIssueInput)
@serialize_pydantic_return
async def update_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    issue_number: int,
    title: str | None = None,
    body: str | None = None,
    state: str | None = None,
    labels: list[str] | None = None,
    assignees: list[str] | None = None,
) -> UpdateIssueOutput:
    """Update an existing issue."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    if state is not None:
        payload["state"] = state
    if labels is not None:
        payload["labels"] = labels
    if assignees is not None:
        payload["assignees"] = assignees
    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        i = response.json()
    return UpdateIssueOutput(
        success=True,
        issue=IssueUpdated(
            number=i.get("number"),
            title=i.get("title"),
            body=i.get("body"),
            state=i.get("state"),
            url=i.get("html_url"),
            updated_at=i.get("updated_at"),
        ),
    )


@tool(args_schema=ListPullRequestsInput)
@serialize_pydantic_return
async def list_pull_requests(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    state: str = "open",
    sort: str = "created",
    direction: str = "desc",
    per_page: int = 30,
    page: int = 1,
) -> ListPullRequestsOutput:
    """List pull requests in a repository."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "per_page": per_page,
        "page": page,
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        prs = response.json()
    return ListPullRequestsOutput(
        success=True,
        pull_requests=[
            PullRequestSummary(
                number=p.get("number"),
                title=p.get("title"),
                body=p.get("body"),
                state=p.get("state"),
                url=p.get("html_url"),
                user=(p.get("user") or {}).get("login"),
                head=(p.get("head") or {}).get("ref"),
                base=(p.get("base") or {}).get("ref"),
                draft=p.get("draft"),
                mergeable=p.get("mergeable"),
                created_at=p.get("created_at"),
                updated_at=p.get("updated_at"),
                merged_at=p.get("merged_at"),
                closed_at=p.get("closed_at"),
            )
            for p in prs
        ],
        total=len(prs),
        page=page,
        per_page=per_page,
    )


@tool(args_schema=CreatePullRequestInput)
@serialize_pydantic_return
async def create_pull_request(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: str | None = None,
    draft: bool = False,
) -> CreatePullRequestOutput:
    """Create a pull request."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"title": title, "head": head, "base": base, "draft": draft}
    if body:
        payload["body"] = body
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/pulls",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        p = response.json()
    return CreatePullRequestOutput(
        success=True,
        pull_request=PullRequestCreated(
            number=p.get("number"),
            title=p.get("title"),
            body=p.get("body"),
            state=p.get("state"),
            url=p.get("html_url"),
            draft=p.get("draft"),
            head=(p.get("head") or {}).get("ref"),
            base=(p.get("base") or {}).get("ref"),
            created_at=p.get("created_at"),
        ),
    )


@tool(args_schema=GetPullRequestInput)
@serialize_pydantic_return
async def get_pull_request(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    pull_number: int,
) -> GetPullRequestOutput:
    """Get a specific pull request."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}",
            headers=headers,
        )
        response.raise_for_status()
        p = response.json()
    return GetPullRequestOutput(
        success=True,
        pull_request=PullRequestDetailed(
            number=p.get("number"),
            title=p.get("title"),
            body=p.get("body"),
            state=p.get("state"),
            url=p.get("html_url"),
            user=(p.get("user") or {}).get("login"),
            head=(p.get("head") or {}).get("ref"),
            base=(p.get("base") or {}).get("ref"),
            draft=p.get("draft"),
            mergeable=p.get("mergeable"),
            merged=p.get("merged"),
            created_at=p.get("created_at"),
            updated_at=p.get("updated_at"),
            merged_at=p.get("merged_at"),
            closed_at=p.get("closed_at"),
            commits=p.get("commits"),
            additions=p.get("additions"),
            deletions=p.get("deletions"),
            changed_files=p.get("changed_files"),
        ),
    )


@tool(args_schema=MergePullRequestInput)
@serialize_pydantic_return
async def merge_pull_request(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    pull_number: int,
    commit_title: str | None = None,
    commit_message: str | None = None,
    merge_method: str = "merge",
) -> MergePullRequestOutput:
    """Merge a pull request."""
    headers = _get_auth_headers(auth_type, auth_data)
    payload: dict[str, Any] = {"merge_method": merge_method}
    if commit_title:
        payload["commit_title"] = commit_title
    if commit_message:
        payload["commit_message"] = commit_message
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}/merge",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()
    return MergePullRequestOutput(
        success=True,
        merged=result.get("merged"),
        message=result.get("message"),
        sha=result.get("sha"),
    )


@tool(args_schema=CreateBranchInput)
@serialize_pydantic_return
async def create_branch(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    branch_name: str,
    from_branch: str = "main",
) -> CreateBranchOutput:
    """Create a new branch from an existing branch."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        ref_response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{from_branch}",
            headers=headers,
        )
        ref_response.raise_for_status()
        base_sha = ref_response.json()["object"]["sha"]

        payload = {"ref": f"refs/heads/{branch_name}", "sha": base_sha}
        response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/git/refs",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        branch = response.json()
    return CreateBranchOutput(
        success=True,
        branch=Branch(
            name=branch_name,
            ref=branch.get("ref"),
            sha=(branch.get("object") or {}).get("sha"),
        ),
    )


@tool(args_schema=GetFileContentInput)
@serialize_pydantic_return
async def get_file_content(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    path: str,
    ref: str | None = None,
) -> GetFileContentOutput:
    """Get content of a file from a repository (content is base64-decoded UTF-8)."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if ref:
        params["ref"] = ref
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        f = response.json()
    raw_b64 = f.get("content") or ""
    decoded = base64.b64decode(raw_b64).decode("utf-8") if raw_b64 else ""
    return GetFileContentOutput(
        success=True,
        file=FileContent(
            name=f.get("name"),
            path=f.get("path"),
            size=f.get("size"),
            content=decoded,
            sha=f.get("sha"),
            download_url=f.get("download_url"),
        ),
    )


@tool(args_schema=CreateCommitInput)
@serialize_pydantic_return
async def create_commit(
    auth_type: str,
    auth_data: dict[str, Any],
    owner: str,
    repo: str,
    branch: str,
    message: str,
    files: list[dict[str, str]],
) -> CreateCommitOutput:
    """Create a commit with file changes on a given branch."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        ref_response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/ref/heads/{branch}",
            headers=headers,
        )
        ref_response.raise_for_status()
        base_sha = ref_response.json()["object"]["sha"]

        commit_response = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/git/commits/{base_sha}",
            headers=headers,
        )
        commit_response.raise_for_status()
        base_tree_sha = commit_response.json()["tree"]["sha"]

        tree_items: list[dict[str, Any]] = []
        for f in files:
            content_b64 = base64.b64encode(f["content"].encode()).decode()
            blob_response = await client.post(
                f"https://api.github.com/repos/{owner}/{repo}/git/blobs",
                headers=headers,
                json={"content": content_b64, "encoding": "base64"},
            )
            blob_response.raise_for_status()
            tree_items.append(
                {
                    "path": f["path"],
                    "mode": "100644",
                    "type": "blob",
                    "sha": blob_response.json()["sha"],
                }
            )

        tree_response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/git/trees",
            headers=headers,
            json={"base_tree": base_tree_sha, "tree": tree_items},
        )
        tree_response.raise_for_status()
        tree_sha = tree_response.json()["sha"]

        commit_create_response = await client.post(
            f"https://api.github.com/repos/{owner}/{repo}/git/commits",
            headers=headers,
            json={"message": message, "tree": tree_sha, "parents": [base_sha]},
        )
        commit_create_response.raise_for_status()
        new_commit_sha = commit_create_response.json()["sha"]

        update_response = await client.patch(
            f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}",
            headers=headers,
            json={"sha": new_commit_sha},
        )
        update_response.raise_for_status()
    return CreateCommitOutput(
        success=True,
        commit=CommitCreated(sha=new_commit_sha, message=message, branch=branch),
    )


@tool(args_schema=SearchCodeInput)
@serialize_pydantic_return
async def search_code(
    auth_type: str,
    auth_data: dict[str, Any],
    query: str,
    sort: str | None = None,
    order: str = "desc",
    per_page: int = 30,
    page: int = 1,
) -> SearchCodeOutput:
    """Search code across repositories."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"q": query, "order": order, "per_page": per_page, "page": page}
    if sort:
        params["sort"] = sort
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/search/code", headers=headers, params=params
        )
        response.raise_for_status()
        results = response.json()
    return SearchCodeOutput(
        success=True,
        total_count=results.get("total_count") or 0,
        items=[
            SearchCodeItem(
                name=item.get("name"),
                path=item.get("path"),
                repository=(item.get("repository") or {}).get("full_name"),
                url=item.get("html_url"),
                sha=item.get("sha"),
            )
            for item in results.get("items") or []
        ],
        page=page,
        per_page=per_page,
    )
