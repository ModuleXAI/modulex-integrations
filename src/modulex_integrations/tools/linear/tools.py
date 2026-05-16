"""Linear LangChain ``@tool`` functions.

GraphQL API (``api.linear.app/graphql``). ``api_key`` is sent as the
raw ``Authorization`` value with no ``Bearer`` prefix — Linear's
documented contract. Filter clauses for ``search_issues`` /
``list_projects`` are interpolated into the GraphQL string verbatim
(matching legacy); values come from internal IDs, not user prose.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.linear.outputs import (
    CreateIssueOutput,
    CreateProjectOutput,
    GetIssueOutput,
    GetTeamsOutput,
    ListProjectsOutput,
    SearchIssuesOutput,
    UpdateIssueOutput,
)

__all__ = [
    "create_issue",
    "create_project",
    "get_issue",
    "get_teams",
    "list_projects",
    "search_issues",
    "update_issue",
]

_API_URL = "https://api.linear.app/graphql"
_TIMEOUT = 30.0


_ISSUE_FRAGMENT = """
fragment IssueFields on Issue {
    id
    identifier
    title
    description
    url
    priority
    priorityLabel
    estimate
    dueDate
    createdAt
    updatedAt
    completedAt
    canceledAt
    archivedAt
    state { id name type }
    team { id name key }
    assignee { id name email }
    creator { id name email }
    project { id name }
    labels { nodes { id name color } }
}
"""

_PROJECT_FRAGMENT = """
fragment ProjectFields on Project {
    id
    name
    description
    url
    color
    state
    priority
    progress
    createdAt
    updatedAt
    startDate
    targetDate
    lead { id name email }
    status { id name }
}
"""

_TEAM_FRAGMENT = """
fragment TeamFields on Team {
    id
    name
    key
    description
    icon
    color
    timezone
    createdAt
    updatedAt
}
"""


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _empty_key_error(name: str) -> str:
    return (
        f"Linear API key is empty for {name}. "
        "Please configure a valid Linear credential."
    )


async def _graphql(
    api_key: str,
    query: str,
    variables: dict[str, Any] | None = None,
) -> tuple[bool, str | None, dict[str, Any] | None]:
    """Execute a GraphQL query/mutation. Returns (ok, error, data)."""
    payload: dict[str, Any] = {"query": query}
    if variables:
        payload["variables"] = variables

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(_API_URL, headers=_headers(api_key), json=payload)
        if response.status_code != 200:
            return False, (
                f"Linear API error: {response.status_code} - {response.text}"
            ), None
        body = response.json() or {}
    except Exception as exc:
        return False, f"GraphQL request failed: {exc}", None

    errors = body.get("errors")
    if errors:
        messages = [e.get("message", str(e)) for e in errors if isinstance(e, dict)]
        return False, f"GraphQL errors: {'; '.join(messages)}", None

    data = body.get("data")
    if not isinstance(data, dict):
        return True, None, None
    return True, None, data


# --- Input schemas ---------------------------------------------------------


class GetTeamsInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    limit: int = Field(default=50, description="Maximum number of teams")


class GetIssueInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    issue_id: str = Field(description="The ID of the issue to retrieve")


class SearchIssuesInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    team_id: str | None = Field(default=None, description="Filter by team ID")
    project_id: str | None = Field(default=None, description="Filter by project ID")
    assignee_id: str | None = Field(default=None, description="Filter by assignee")
    state_id: str | None = Field(default=None, description="Filter by workflow state")
    query: str | None = Field(default=None, description="Substring match in titles")
    label_names: list[str] | None = Field(default=None, description="Filter by labels")
    include_archived: bool = Field(default=False, description="Include archived issues")
    order_by: str | None = Field(default="updatedAt", description="Order field")
    limit: int = Field(default=50, description="Maximum number of issues")


class CreateIssueInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    team_id: str = Field(description="The ID of the team for the new issue")
    title: str = Field(description="The title of the new issue")
    description: str | None = Field(default=None, description="Markdown body")
    assignee_id: str | None = Field(default=None, description="Assignee user ID")
    project_id: str | None = Field(default=None, description="Project ID")
    state_id: str | None = Field(default=None, description="Workflow state ID")
    label_ids: list[str] | None = Field(default=None, description="Label IDs")
    priority: int | None = Field(default=None, description="Priority (0-4)")


class UpdateIssueInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    issue_id: str = Field(description="The ID of the issue to update")
    title: str | None = Field(default=None, description="New title")
    description: str | None = Field(default=None, description="New markdown body")
    assignee_id: str | None = Field(default=None, description="New assignee user ID")
    team_id: str | None = Field(default=None, description="Move to a different team")
    project_id: str | None = Field(default=None, description="Move to a different project")
    state_id: str | None = Field(default=None, description="Change workflow state")
    label_ids: list[str] | None = Field(default=None, description="Replace labels")
    priority: int | None = Field(default=None, description="New priority (0-4)")


class ListProjectsInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    team_id: str | None = Field(default=None, description="Filter by team ID")
    order_by: str | None = Field(default="updatedAt", description="Order field")
    limit: int = Field(default=50, description="Maximum number of projects")
    after: str | None = Field(default=None, description="Pagination cursor")


class CreateProjectInput(BaseModel):
    api_key: str = Field(description="Linear API key (provided by credential system)")
    team_id: str = Field(description="The ID of the team for the new project")
    name: str = Field(description="The name of the new project")
    description: str | None = Field(default=None, description="Description")
    status_id: str | None = Field(default=None, description="Status ID")
    priority: int | None = Field(default=None, description="Priority (0-4)")
    member_ids: list[str] | None = Field(default=None, description="Member user IDs")
    start_date: str | None = Field(default=None, description="Start date YYYY-MM-DD")
    target_date: str | None = Field(default=None, description="Target date YYYY-MM-DD")
    label_ids: list[str] | None = Field(default=None, description="Label IDs")


# --- Tools -----------------------------------------------------------------


@tool(args_schema=GetTeamsInput)
@serialize_pydantic_return
async def get_teams(api_key: str, limit: int = 50) -> GetTeamsOutput:
    """List all teams in the Linear workspace."""
    if not api_key or not api_key.strip():
        return GetTeamsOutput(success=False, error=_empty_key_error("get_teams"))

    query = f"""
        query GetTeams($first: Int!) {{
            teams(first: $first) {{
                nodes {{ ...TeamFields }}
                pageInfo {{ hasNextPage endCursor }}
            }}
        }}
        {_TEAM_FRAGMENT}
    """
    ok, err, data = await _graphql(api_key, query, {"first": limit})
    if not ok or data is None:
        return GetTeamsOutput(success=False, error=err)

    teams_obj = data.get("teams") or {}
    teams = teams_obj.get("nodes") or []
    return GetTeamsOutput(
        success=True,
        teams=teams,
        count=len(teams),
        page_info=teams_obj.get("pageInfo"),
    )


@tool(args_schema=GetIssueInput)
@serialize_pydantic_return
async def get_issue(api_key: str, issue_id: str) -> GetIssueOutput:
    """Get a Linear issue by its ID."""
    if not api_key or not api_key.strip():
        return GetIssueOutput(success=False, error=_empty_key_error("get_issue"))

    query = f"""
        query GetIssue($issueId: String!) {{
            issue(id: $issueId) {{ ...IssueFields }}
        }}
        {_ISSUE_FRAGMENT}
    """
    ok, err, data = await _graphql(api_key, query, {"issueId": issue_id})
    if not ok or data is None:
        return GetIssueOutput(success=False, error=err)

    issue = data.get("issue")
    if not issue:
        return GetIssueOutput(success=False, error=f"Issue {issue_id} not found")
    return GetIssueOutput(success=True, issue=issue)


def _build_search_filter(
    query: str | None,
    team_id: str | None,
    project_id: str | None,
    assignee_id: str | None,
    state_id: str | None,
    label_names: list[str] | None,
) -> str:
    parts: list[str] = []
    if query:
        parts.append(f'title: {{ containsIgnoreCase: "{query}" }}')
    if team_id:
        parts.append(f'team: {{ id: {{ eq: "{team_id}" }} }}')
    if project_id:
        parts.append(f'project: {{ id: {{ eq: "{project_id}" }} }}')
    if assignee_id:
        parts.append(f'assignee: {{ id: {{ eq: "{assignee_id}" }} }}')
    if state_id:
        parts.append(f'state: {{ id: {{ eq: "{state_id}" }} }}')
    if label_names:
        names = ", ".join(f'"{name}"' for name in label_names)
        parts.append(f'labels: {{ name: {{ in: [{names}] }} }}')
    return ", ".join(parts)


@tool(args_schema=SearchIssuesInput)
@serialize_pydantic_return
async def search_issues(
    api_key: str,
    team_id: str | None = None,
    project_id: str | None = None,
    assignee_id: str | None = None,
    state_id: str | None = None,
    query: str | None = None,
    label_names: list[str] | None = None,
    include_archived: bool = False,
    order_by: str | None = "updatedAt",
    limit: int = 50,
) -> SearchIssuesOutput:
    """Search Linear issues with filters."""
    if not api_key or not api_key.strip():
        return SearchIssuesOutput(success=False, error=_empty_key_error("search_issues"))

    filter_str = _build_search_filter(
        query, team_id, project_id, assignee_id, state_id, label_names
    )
    filter_clause = f"filter: {{ {filter_str} }}" if filter_str else ""

    graphql_query = f"""
        query SearchIssues($first: Int!, $includeArchived: Boolean, $orderBy: PaginationOrderBy) {{
            issues(
                first: $first
                {filter_clause}
                includeArchived: $includeArchived
                orderBy: $orderBy
            ) {{
                nodes {{ ...IssueFields }}
                pageInfo {{ hasNextPage endCursor }}
            }}
        }}
        {_ISSUE_FRAGMENT}
    """

    ok, err, data = await _graphql(
        api_key,
        graphql_query,
        {"first": limit, "includeArchived": include_archived, "orderBy": order_by},
    )
    if not ok or data is None:
        return SearchIssuesOutput(success=False, error=err)

    issues_obj = data.get("issues") or {}
    issues = issues_obj.get("nodes") or []
    return SearchIssuesOutput(
        success=True,
        issues=issues,
        count=len(issues),
        page_info=issues_obj.get("pageInfo"),
    )


@tool(args_schema=CreateIssueInput)
@serialize_pydantic_return
async def create_issue(
    api_key: str,
    team_id: str,
    title: str,
    description: str | None = None,
    assignee_id: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    label_ids: list[str] | None = None,
    priority: int | None = None,
) -> CreateIssueOutput:
    """Create a new Linear issue."""
    if not api_key or not api_key.strip():
        return CreateIssueOutput(success=False, error=_empty_key_error("create_issue"))

    mutation = f"""
        mutation CreateIssue($input: IssueCreateInput!) {{
            issueCreate(input: $input) {{
                success
                issue {{ ...IssueFields }}
            }}
        }}
        {_ISSUE_FRAGMENT}
    """

    input_data: dict[str, Any] = {"teamId": team_id, "title": title}
    if description:
        input_data["description"] = description
    if assignee_id:
        input_data["assigneeId"] = assignee_id
    if project_id:
        input_data["projectId"] = project_id
    if state_id:
        input_data["stateId"] = state_id
    if label_ids:
        input_data["labelIds"] = label_ids
    if priority is not None:
        input_data["priority"] = priority

    ok, err, data = await _graphql(api_key, mutation, {"input": input_data})
    if not ok or data is None:
        return CreateIssueOutput(success=False, error=err)

    result = data.get("issueCreate") or {}
    if not result.get("success"):
        return CreateIssueOutput(success=False, error="Failed to create issue")
    return CreateIssueOutput(success=True, issue=result.get("issue"))


@tool(args_schema=UpdateIssueInput)
@serialize_pydantic_return
async def update_issue(
    api_key: str,
    issue_id: str,
    title: str | None = None,
    description: str | None = None,
    assignee_id: str | None = None,
    team_id: str | None = None,
    project_id: str | None = None,
    state_id: str | None = None,
    label_ids: list[str] | None = None,
    priority: int | None = None,
) -> UpdateIssueOutput:
    """Update an existing Linear issue."""
    if not api_key or not api_key.strip():
        return UpdateIssueOutput(success=False, error=_empty_key_error("update_issue"))

    input_data: dict[str, Any] = {}
    if title is not None:
        input_data["title"] = title
    if description is not None:
        input_data["description"] = description
    if assignee_id is not None:
        input_data["assigneeId"] = assignee_id
    if team_id is not None:
        input_data["teamId"] = team_id
    if project_id is not None:
        input_data["projectId"] = project_id
    if state_id is not None:
        input_data["stateId"] = state_id
    if label_ids is not None:
        input_data["labelIds"] = label_ids
    if priority is not None:
        input_data["priority"] = priority

    if not input_data:
        return UpdateIssueOutput(success=False, error="No update fields provided")

    mutation = f"""
        mutation UpdateIssue($issueId: String!, $input: IssueUpdateInput!) {{
            issueUpdate(id: $issueId, input: $input) {{
                success
                issue {{ ...IssueFields }}
            }}
        }}
        {_ISSUE_FRAGMENT}
    """

    ok, err, data = await _graphql(
        api_key, mutation, {"issueId": issue_id, "input": input_data}
    )
    if not ok or data is None:
        return UpdateIssueOutput(success=False, error=err)

    result = data.get("issueUpdate") or {}
    if not result.get("success"):
        return UpdateIssueOutput(success=False, error="Failed to update issue")
    return UpdateIssueOutput(success=True, issue=result.get("issue"))


@tool(args_schema=ListProjectsInput)
@serialize_pydantic_return
async def list_projects(
    api_key: str,
    team_id: str | None = None,
    order_by: str | None = "updatedAt",
    limit: int = 50,
    after: str | None = None,
) -> ListProjectsOutput:
    """List Linear projects with optional team filter + pagination."""
    if not api_key or not api_key.strip():
        return ListProjectsOutput(success=False, error=_empty_key_error("list_projects"))

    filter_clause = (
        f'filter: {{ accessibleTeams: {{ id: {{ eq: "{team_id}" }} }} }}'
        if team_id
        else ""
    )
    after_clause = f', after: "{after}"' if after else ""

    graphql_query = f"""
        query ListProjects($first: Int!, $orderBy: PaginationOrderBy) {{
            projects(
                first: $first
                {filter_clause}
                orderBy: $orderBy
                {after_clause}
            ) {{
                nodes {{ ...ProjectFields }}
                pageInfo {{ hasNextPage endCursor }}
            }}
        }}
        {_PROJECT_FRAGMENT}
    """

    ok, err, data = await _graphql(
        api_key, graphql_query, {"first": limit, "orderBy": order_by}
    )
    if not ok or data is None:
        return ListProjectsOutput(success=False, error=err)

    projects_obj = data.get("projects") or {}
    projects = projects_obj.get("nodes") or []
    return ListProjectsOutput(
        success=True,
        projects=projects,
        count=len(projects),
        page_info=projects_obj.get("pageInfo"),
    )


@tool(args_schema=CreateProjectInput)
@serialize_pydantic_return
async def create_project(
    api_key: str,
    team_id: str,
    name: str,
    description: str | None = None,
    status_id: str | None = None,
    priority: int | None = None,
    member_ids: list[str] | None = None,
    start_date: str | None = None,
    target_date: str | None = None,
    label_ids: list[str] | None = None,
) -> CreateProjectOutput:
    """Create a new Linear project."""
    if not api_key or not api_key.strip():
        return CreateProjectOutput(
            success=False, error=_empty_key_error("create_project")
        )

    mutation = f"""
        mutation CreateProject($input: ProjectCreateInput!) {{
            projectCreate(input: $input) {{
                success
                project {{ ...ProjectFields }}
            }}
        }}
        {_PROJECT_FRAGMENT}
    """

    input_data: dict[str, Any] = {"teamIds": [team_id], "name": name}
    if description:
        input_data["description"] = description
    if status_id:
        input_data["statusId"] = status_id
    if priority is not None:
        input_data["priority"] = priority
    if member_ids:
        input_data["memberIds"] = member_ids
    if start_date:
        input_data["startDate"] = start_date
    if target_date:
        input_data["targetDate"] = target_date
    if label_ids:
        input_data["labelIds"] = label_ids

    ok, err, data = await _graphql(api_key, mutation, {"input": input_data})
    if not ok or data is None:
        return CreateProjectOutput(success=False, error=err)

    result = data.get("projectCreate") or {}
    if not result.get("success"):
        return CreateProjectOutput(success=False, error="Failed to create project")
    return CreateProjectOutput(success=True, project=result.get("project"))
