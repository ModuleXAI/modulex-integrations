"""GitLab LangChain @tool functions."""
from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.gitlab.outputs import (
    BranchCommit,
    BranchSummary,
    CommitSummary,
    CreateBranchOutput,
    CreateEpicOutput,
    CreateIssueOutput,
    EpicSummary,
    GetIssueOutput,
    GetRepoBranchOutput,
    GroupSummary,
    IssueSummary,
    ListCommitsOutput,
    ListGroupsOutput,
    ListProjectMembersOutput,
    ListRepoBranchesOutput,
    MemberSummary,
    SearchIssuesOutput,
    UpdateEpicOutput,
    UpdateIssueOutput,
)

__all__ = [
    "create_branch",
    "create_epic",
    "create_issue",
    "get_issue",
    "get_repo_branch",
    "list_commits",
    "list_groups",
    "list_project_members",
    "list_repo_branches",
    "search_issues",
    "update_epic",
    "update_issue",
]

_BASE_URL = "https://gitlab.com/api/v4"


def _get_auth_headers(auth_type: str, auth_data: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {"Accept": "application/json"}
    if auth_type == "oauth2":
        access_token = auth_data.get("access_token")
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
    return headers


def _parse_branch(b: dict[str, Any]) -> BranchSummary:
    c = b.get("commit") or {}
    return BranchSummary(
        name=b.get("name"),
        commit=BranchCommit(
            id=c.get("id"),
            short_id=c.get("short_id"),
            title=c.get("title"),
            author_name=c.get("author_name"),
            author_email=c.get("author_email"),
            created_at=c.get("created_at"),
            message=c.get("message"),
        ),
        merged=b.get("merged"),
        protected=b.get("protected"),
        developers_can_push=b.get("developers_can_push"),
        developers_can_merge=b.get("developers_can_merge"),
        can_push=b.get("can_push"),
        web_url=b.get("web_url"),
    )


def _parse_issue(i: dict[str, Any]) -> IssueSummary:
    return IssueSummary(
        id=i.get("id"),
        iid=i.get("iid"),
        project_id=i.get("project_id"),
        title=i.get("title"),
        description=i.get("description"),
        state=i.get("state"),
        web_url=i.get("web_url"),
        created_at=i.get("created_at"),
        updated_at=i.get("updated_at"),
        closed_at=i.get("closed_at"),
        labels=i.get("labels") or [],
        assignees=[
            a.get("username", "") for a in (i.get("assignees") or []) if a.get("username")
        ],
    )


def _parse_epic(e: dict[str, Any]) -> EpicSummary:
    return EpicSummary(
        id=e.get("id"),
        iid=e.get("iid"),
        group_id=e.get("group_id"),
        title=e.get("title"),
        description=e.get("description"),
        state=e.get("state"),
        confidential=e.get("confidential"),
        web_url=e.get("web_url"),
        created_at=e.get("created_at"),
        updated_at=e.get("updated_at"),
        labels=e.get("labels") or [],
    )


# --- Input schemas --------------------------------------------------------


class CreateBranchInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    ref: str = Field(description="The branch name or commit SHA to create the new branch from")
    branch_name: str = Field(description="The name of the branch to create")


class CreateEpicInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="The ID of the group")
    title: str = Field(description="The title of the epic")
    description: str | None = Field(default=None, description="The description of the epic")
    labels: list[str] | None = Field(default=None, description="List of label names for the epic")
    parent_id: str | None = Field(default=None, description="The internal ID of the parent epic (requires GitLab Premium or Ultimate)")
    color: str | None = Field(default=None, description="The color of the epic (introduced in GitLab 14.8)")
    confidential: bool | None = Field(default=None, description="Whether the epic should be confidential")
    created_at: str | None = Field(default=None, description="When the epic was created, ISO 8601 format (requires admin or owner privileges)")
    start_date_is_fixed: bool | None = Field(default=None, description="Whether start date should be sourced from start_date_fixed or from milestones")
    due_date_is_fixed: bool | None = Field(default=None, description="Whether due date should be sourced from due_date_fixed or from milestones")
    start_date_fixed: str | None = Field(default=None, description="The fixed start date of the epic, ISO 8601 format")
    due_date_fixed: str | None = Field(default=None, description="The fixed due date of the epic, ISO 8601 format")


class CreateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    title: str = Field(description="The title of the issue")
    description: str | None = Field(default=None, description="The description of the issue")
    labels: list[str] | None = Field(default=None, description="List of label names for the issue")
    assignee_ids: list[str] | None = Field(default=None, description="List of user IDs to assign the issue to")


class GetIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    issue_iid: str = Field(description="The internal ID of the project issue")


class GetRepoBranchInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    branch: str = Field(description="The name of the branch")


class ListCommitsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    ref_name: str | None = Field(default=None, description="The name of a repository branch, tag, or revision range; defaults to the default branch if not given")
    max: int = Field(default=100, description="Maximum number of commits to return (per_page)")


class ListGroupsInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    min_access_level: int | None = Field(default=None, description="Limit to groups where the user has at least this access level: 10 (Guest), 20 (Reporter), 30 (Developer), 40 (Maintainer), 50 (Owner)")
    top_level_only: bool | None = Field(default=None, description="Limit to top-level groups, excluding all subgroups")
    search: str | None = Field(default=None, description="Return groups matching this search string")
    order_by: str | None = Field(default=None, description="Order groups by: name, path, id, or similarity (must be similarity when search is provided)")
    sort: str = Field(default="asc", description="Sort order: asc or desc")
    active: bool | None = Field(default=None, description="Limit to groups that are not archived and not marked for deletion")
    archived: bool | None = Field(default=None, description="Limit to groups that are archived")


class ListProjectMembersInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    query: str | None = Field(default=None, description="Filter results by name, email, or username (partial values accepted)")
    user_ids: list[str] | None = Field(default=None, description="List of user IDs to filter results to")
    skip_users: list[str] | None = Field(default=None, description="List of user IDs to exclude from results")
    show_seat_info: bool | None = Field(default=None, description="Return seat information for each member if available")


class ListRepoBranchesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    search: str | None = Field(default=None, description="Return branches containing this search string")


class SearchIssuesInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    search: str | None = Field(default=None, description="Search issues against their title and description")
    labels: list[str] | None = Field(default=None, description="List of label names; issues must have all labels to be returned")
    state: str = Field(default="all", description="Return issues by state: all, opened, or closed")
    assignee_id: str | None = Field(default=None, description="Return issues assigned to the given user ID")
    max: int = Field(default=100, description="Maximum number of issues to return (per_page)")


class UpdateEpicInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    group_id: str = Field(description="The ID of the group")
    epic_iid: str = Field(description="The internal ID of the epic")
    title: str | None = Field(default=None, description="The title of the epic")
    description: str | None = Field(default=None, description="The description of the epic")
    labels: list[str] | None = Field(default=None, description="List of label names for the epic (set empty to unassign all)")
    add_labels: list[str] | None = Field(default=None, description="Labels to add to the epic")
    remove_labels: list[str] | None = Field(default=None, description="Labels to remove from the epic")
    parent_id: str | None = Field(default=None, description="The ID of a parent epic (available in GitLab 14.6+)")
    state_event: str | None = Field(default=None, description="State event for the epic: close or reopen")
    confidential: bool | None = Field(default=None, description="Whether the epic should be confidential")
    color: str | None = Field(default=None, description="The color of the epic")
    updated_at: str | None = Field(default=None, description="When the epic was updated, ISO 8601 format (requires admin or owner privileges)")
    start_date_is_fixed: bool | None = Field(default=None, description="Whether start date should be sourced from start_date_fixed or from milestones")
    due_date_is_fixed: bool | None = Field(default=None, description="Whether due date should be sourced from due_date_fixed or from milestones")
    start_date_fixed: str | None = Field(default=None, description="The fixed start date of the epic, ISO 8601 format")
    due_date_fixed: str | None = Field(default=None, description="The fixed due date of the epic, ISO 8601 format")


class UpdateIssueInput(BaseModel):
    auth_type: str = Field(description="Authentication type")
    auth_data: dict[str, Any] = Field(description="Authentication data")
    project_id: int = Field(description="The project ID, as displayed in the main project page")
    issue_iid: str = Field(description="The internal ID of the issue")
    title: str | None = Field(default=None, description="The title of the issue")
    description: str | None = Field(default=None, description="The description of the issue")
    labels: list[str] | None = Field(default=None, description="List of label names for the issue (set empty to unassign all)")
    assignee_ids: list[str] | None = Field(default=None, description="List of user IDs to assign the issue to (set to 0 or empty to unassign all)")
    state_event: str | None = Field(default=None, description="State event for the issue: close or reopen")
    discussion_locked: bool | None = Field(default=None, description="Whether the issue discussion is locked")


# --- @tool functions ------------------------------------------------------


@tool(args_schema=CreateBranchInput)
@serialize_pydantic_return
async def create_branch(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    ref: str,
    branch_name: str,
) -> CreateBranchOutput:
    """Create a new branch in a GitLab repository."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/projects/{project_id}/repository/branches",
            headers=headers,
            params={"branch": branch_name, "ref": ref},
        )
        response.raise_for_status()
        data = response.json()
    return CreateBranchOutput(success=True, branch=_parse_branch(data))


@tool(args_schema=CreateEpicInput)
@serialize_pydantic_return
async def create_epic(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    title: str,
    description: str | None = None,
    labels: list[str] | None = None,
    parent_id: str | None = None,
    color: str | None = None,
    confidential: bool | None = None,
    created_at: str | None = None,
    start_date_is_fixed: bool | None = None,
    due_date_is_fixed: bool | None = None,
    start_date_fixed: str | None = None,
    due_date_fixed: str | None = None,
) -> CreateEpicOutput:
    """Create a new epic in a GitLab group (requires GitLab Premium or Ultimate)."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"title": title}
    if description is not None:
        body["description"] = description
    if labels is not None:
        body["labels"] = ",".join(labels)
    if parent_id is not None:
        body["parent_id"] = parent_id
    if color is not None:
        body["color"] = color
    if confidential is not None:
        body["confidential"] = confidential
    if created_at is not None:
        body["created_at"] = created_at
    if start_date_is_fixed is not None:
        body["start_date_is_fixed"] = start_date_is_fixed
    if due_date_is_fixed is not None:
        body["due_date_is_fixed"] = due_date_is_fixed
    if start_date_fixed is not None:
        body["start_date_fixed"] = start_date_fixed
    if due_date_fixed is not None:
        body["due_date_fixed"] = due_date_fixed
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/groups/{group_id}/epics",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return CreateEpicOutput(success=True, epic=_parse_epic(data))


@tool(args_schema=CreateIssueInput)
@serialize_pydantic_return
async def create_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    title: str,
    description: str | None = None,
    labels: list[str] | None = None,
    assignee_ids: list[str] | None = None,
) -> CreateIssueOutput:
    """Create a new issue in a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {"title": title}
    if description is not None:
        body["description"] = description
    if labels is not None:
        body["labels"] = ",".join(labels)
    if assignee_ids is not None:
        body["assignee_ids"] = [int(uid) for uid in assignee_ids]
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_BASE_URL}/projects/{project_id}/issues",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return CreateIssueOutput(success=True, issue=_parse_issue(data))


@tool(args_schema=GetIssueInput)
@serialize_pydantic_return
async def get_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    issue_iid: str,
) -> GetIssueOutput:
    """Get a single issue from a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/projects/{project_id}/issues/{issue_iid}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetIssueOutput(success=True, issue=_parse_issue(data))


@tool(args_schema=GetRepoBranchInput)
@serialize_pydantic_return
async def get_repo_branch(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    branch: str,
) -> GetRepoBranchOutput:
    """Get a single repository branch from a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    encoded_branch = quote(branch, safe="")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/projects/{project_id}/repository/branches/{encoded_branch}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
    return GetRepoBranchOutput(success=True, branch=_parse_branch(data))


@tool(args_schema=ListCommitsInput)
@serialize_pydantic_return
async def list_commits(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    ref_name: str | None = None,
    max: int = 100,
) -> ListCommitsOutput:
    """List commits in a GitLab repository branch."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"per_page": max}
    if ref_name is not None:
        params["ref_name"] = ref_name
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/projects/{project_id}/repository/commits",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return ListCommitsOutput(
        success=True,
        commits=[
            CommitSummary(
                id=c.get("id"),
                short_id=c.get("short_id"),
                title=c.get("title"),
                author_name=c.get("author_name"),
                author_email=c.get("author_email"),
                authored_date=c.get("authored_date"),
                committed_date=c.get("committed_date"),
                message=c.get("message"),
                web_url=c.get("web_url"),
            )
            for c in data
        ],
    )


@tool(args_schema=ListGroupsInput)
@serialize_pydantic_return
async def list_groups(
    auth_type: str,
    auth_data: dict[str, Any],
    min_access_level: int | None = None,
    top_level_only: bool | None = None,
    search: str | None = None,
    order_by: str | None = None,
    sort: str = "asc",
    active: bool | None = None,
    archived: bool | None = None,
) -> ListGroupsOutput:
    """List all groups accessible to the authenticated user."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {"sort": sort}
    if min_access_level is not None:
        params["min_access_level"] = min_access_level
    if top_level_only is not None:
        params["top_level_only"] = top_level_only
    if search is not None:
        params["search"] = search
    if order_by is not None:
        params["order_by"] = order_by
    if active is not None:
        params["active"] = active
    if archived is not None:
        params["archived"] = archived
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/groups",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return ListGroupsOutput(
        success=True,
        groups=[
            GroupSummary(
                id=g.get("id"),
                name=g.get("name"),
                path=g.get("path"),
                description=g.get("description"),
                visibility=g.get("visibility"),
                web_url=g.get("web_url"),
                full_name=g.get("full_name"),
                full_path=g.get("full_path"),
            )
            for g in data
        ],
    )


@tool(args_schema=ListProjectMembersInput)
@serialize_pydantic_return
async def list_project_members(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    query: str | None = None,
    user_ids: list[str] | None = None,
    skip_users: list[str] | None = None,
    show_seat_info: bool | None = None,
) -> ListProjectMembersOutput:
    """List all members of a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if query is not None:
        params["query"] = query
    if user_ids is not None:
        params["user_ids[]"] = user_ids
    if skip_users is not None:
        params["skip_users[]"] = skip_users
    if show_seat_info is not None:
        params["show_seat_info"] = show_seat_info
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/projects/{project_id}/members",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return ListProjectMembersOutput(
        success=True,
        members=[
            MemberSummary(
                id=m.get("id"),
                username=m.get("username"),
                name=m.get("name"),
                state=m.get("state"),
                access_level=m.get("access_level"),
                web_url=m.get("web_url"),
            )
            for m in data
        ],
    )


@tool(args_schema=ListRepoBranchesInput)
@serialize_pydantic_return
async def list_repo_branches(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    search: str | None = None,
) -> ListRepoBranchesOutput:
    """Get a list of repository branches from a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {}
    if search is not None:
        params["search"] = search
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/projects/{project_id}/repository/branches",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return ListRepoBranchesOutput(
        success=True,
        branches=[_parse_branch(b) for b in data],
    )


@tool(args_schema=SearchIssuesInput)
@serialize_pydantic_return
async def search_issues(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    search: str | None = None,
    labels: list[str] | None = None,
    state: str = "all",
    assignee_id: str | None = None,
    max: int = 100,
) -> SearchIssuesOutput:
    """Search for issues in a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    params: dict[str, Any] = {
        "scope": "all",
        "state": state,
        "per_page": max,
    }
    if search is not None:
        params["search"] = search
    if labels is not None:
        params["labels"] = ",".join(labels)
    if assignee_id is not None:
        params["assignee_id"] = assignee_id
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{_BASE_URL}/projects/{project_id}/issues",
            headers=headers,
            params=params,
        )
        response.raise_for_status()
        data = response.json()
    return SearchIssuesOutput(
        success=True,
        issues=[_parse_issue(i) for i in data],
    )


@tool(args_schema=UpdateEpicInput)
@serialize_pydantic_return
async def update_epic(
    auth_type: str,
    auth_data: dict[str, Any],
    group_id: str,
    epic_iid: str,
    title: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    add_labels: list[str] | None = None,
    remove_labels: list[str] | None = None,
    parent_id: str | None = None,
    state_event: str | None = None,
    confidential: bool | None = None,
    color: str | None = None,
    updated_at: str | None = None,
    start_date_is_fixed: bool | None = None,
    due_date_is_fixed: bool | None = None,
    start_date_fixed: str | None = None,
    due_date_fixed: str | None = None,
) -> UpdateEpicOutput:
    """Update an existing epic in a GitLab group (requires GitLab Premium or Ultimate)."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if labels is not None:
        body["labels"] = ",".join(labels)
    if add_labels is not None:
        body["add_labels"] = ",".join(add_labels)
    if remove_labels is not None:
        body["remove_labels"] = ",".join(remove_labels)
    if parent_id is not None:
        body["parent_id"] = parent_id
    if state_event is not None:
        body["state_event"] = state_event
    if confidential is not None:
        body["confidential"] = confidential
    if color is not None:
        body["color"] = color
    if updated_at is not None:
        body["updated_at"] = updated_at
    if start_date_is_fixed is not None:
        body["start_date_is_fixed"] = start_date_is_fixed
    if due_date_is_fixed is not None:
        body["due_date_is_fixed"] = due_date_is_fixed
    if start_date_fixed is not None:
        body["start_date_fixed"] = start_date_fixed
    if due_date_fixed is not None:
        body["due_date_fixed"] = due_date_fixed
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/groups/{group_id}/epics/{epic_iid}",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return UpdateEpicOutput(success=True, epic=_parse_epic(data))


@tool(args_schema=UpdateIssueInput)
@serialize_pydantic_return
async def update_issue(
    auth_type: str,
    auth_data: dict[str, Any],
    project_id: int,
    issue_iid: str,
    title: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    assignee_ids: list[str] | None = None,
    state_event: str | None = None,
    discussion_locked: bool | None = None,
) -> UpdateIssueOutput:
    """Update an existing issue in a GitLab project."""
    headers = _get_auth_headers(auth_type, auth_data)
    body: dict[str, Any] = {}
    if title is not None:
        body["title"] = title
    if description is not None:
        body["description"] = description
    if labels is not None:
        body["labels"] = ",".join(labels)
    if assignee_ids is not None:
        body["assignee_ids"] = [int(uid) for uid in assignee_ids]
    if state_event is not None:
        body["state_event"] = state_event
    if discussion_locked is not None:
        body["discussion_locked"] = discussion_locked
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{_BASE_URL}/projects/{project_id}/issues/{issue_iid}",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
    return UpdateIssueOutput(success=True, issue=_parse_issue(data))
