"""Railway LangChain ``@tool`` functions.

Twenty async tools wrapping Railway's public GraphQL API
(``https://backboard.railway.com/graphql/v2``). The calling convention
is *key-based*: the modulex ``ToolExecutor`` injects an ``api_key: str``
directly (resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair.

Token type: callers pass an optional ``token_type`` of ``"account"``
(the default — covers account, workspace, and OAuth tokens, sent as
``Authorization: Bearer <key>``) or ``"project"`` (a project-scoped
token, sent as ``Project-Access-Token: <key>``).

Error model: Railway's GraphQL endpoint answers HTTP 200 even for
logical failures, returning them in a top-level ``errors`` array. Each
tool surfaces those as ``success=False`` + ``error`` (the first error
message), and likewise turns non-2xx responses, timeouts, and unexpected
exceptions into ``success=False`` rather than raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.railway.outputs import (
    CreatedResource,
    CreateEnvironmentOutput,
    CreateProjectOutput,
    CreateServiceOutput,
    DeleteEnvironmentOutput,
    DeleteProjectOutput,
    DeleteServiceOutput,
    DeleteVariableOutput,
    DeploymentDetail,
    DeploymentLog,
    DeploymentSummary,
    DeployServiceOutput,
    GetDeploymentLogsOutput,
    GetDeploymentOutput,
    GetProjectOutput,
    ListDeploymentsOutput,
    ListProjectMembersOutput,
    ListProjectsOutput,
    ListVariablesOutput,
    PageInfo,
    ProjectDetail,
    ProjectEnvironment,
    ProjectMember,
    ProjectService,
    ProjectSummary,
    RestartDeploymentOutput,
    RollbackDeploymentOutput,
    TransferProjectOutput,
    UpdatedProject,
    UpdateProjectOutput,
    UpsertVariableOutput,
)

__all__ = [
    "create_environment",
    "create_project",
    "create_service",
    "delete_environment",
    "delete_project",
    "delete_service",
    "delete_variable",
    "deploy_service",
    "get_deployment",
    "get_deployment_logs",
    "get_project",
    "list_deployments",
    "list_project_members",
    "list_projects",
    "list_variables",
    "restart_deployment",
    "rollback_deployment",
    "transfer_project",
    "update_project",
    "upsert_variable",
]

_RAILWAY_GRAPHQL_URL = "https://backboard.railway.com/graphql/v2"
_TIMEOUT = 30.0


# --- Auth + request helpers ------------------------------------------------


def _headers(api_key: str, token_type: str) -> dict[str, str]:
    """Build request headers, switching on token type.

    Project-scoped tokens authenticate with the ``Project-Access-Token``
    header; account, workspace, and OAuth tokens use ``Authorization:
    Bearer``.
    """
    if token_type == "project":
        return {
            "Content-Type": "application/json",
            "Project-Access-Token": api_key,
        }
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }


def _optional(value: str | None) -> str | None:
    """Mirror the upstream ``optionalString`` helper: trim and drop empties."""
    if value is None:
        return None
    trimmed = value.strip()
    return trimmed or None


class _GraphqlError(Exception):
    """Raised internally when Railway returns a GraphQL ``errors`` array."""


async def _execute(query: str, variables: dict[str, Any], api_key: str, token_type: str) -> Any:
    """POST a GraphQL operation and return ``data`` or raise.

    Raises ``_GraphqlError`` for non-2xx responses and for 200 responses
    that carry a top-level ``errors`` array, with the first error message.
    """
    body: dict[str, Any] = {"query": query, "variables": variables}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        response = await client.post(
            _RAILWAY_GRAPHQL_URL,
            headers=_headers(api_key, token_type),
            json=body,
        )
    if response.status_code != 200:
        raise _GraphqlError(f"Railway API error ({response.status_code}): {response.text}")
    payload = response.json()
    errors = payload.get("errors")
    if errors:
        message = errors[0].get("message") if isinstance(errors[0], dict) else None
        raise _GraphqlError(message or "Railway API returned a GraphQL error")
    return payload.get("data") or {}


# --- Input schemas (args_schema for each @tool) ----------------------------

_TOKEN_TYPE_DESC = (
    'Railway token type. Use "account" for account, workspace, or OAuth '
    'tokens, or "project" for project tokens.'
)


class ListProjectsInput(BaseModel):
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    workspace_id: str | None = Field(default=None, description="Workspace ID to list projects from")
    first: int | None = Field(default=None, description="Maximum number of projects to return")
    after: str | None = Field(default=None, description="Cursor for pagination")


class GetProjectInput(BaseModel):
    api_key: str = Field(description="Railway API token (provided by credential system)")
    project_id: str = Field(description="Railway project ID")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class CreateProjectInput(BaseModel):
    name: str = Field(description="Project name")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    description: str | None = Field(default=None, description="Project description")
    workspace_id: str | None = Field(
        default=None, description="Workspace ID to create the project in"
    )
    is_public: bool | None = Field(
        default=None, description="Whether the project should be publicly visible"
    )
    default_environment_name: str | None = Field(
        default=None, description="Name for the default environment"
    )
    pr_deploys: bool | None = Field(
        default=None, description="Whether to enable pull request deploys"
    )


class UpdateProjectInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    name: str | None = Field(default=None, description="Updated project name")
    description: str | None = Field(default=None, description="Updated project description")
    is_public: bool | None = Field(
        default=None, description="Whether the project should be publicly visible"
    )
    pr_deploys: bool | None = Field(
        default=None, description="Whether to enable pull request deploy environments"
    )


class DeleteProjectInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class TransferProjectInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    workspace_id: str = Field(description="Destination workspace ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class ListProjectMembersInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class CreateEnvironmentInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    name: str = Field(description="Environment name")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    source_environment_id: str | None = Field(
        default=None, description="Environment ID to clone from"
    )
    ephemeral: bool | None = Field(default=None, description="Whether the environment is ephemeral")
    skip_initial_deploys: bool | None = Field(
        default=None, description="Whether to skip initial deploys for the environment"
    )
    stage_initial_changes: bool | None = Field(
        default=None,
        description="Whether to stage initial changes instead of applying them immediately",
    )


class DeleteEnvironmentInput(BaseModel):
    environment_id: str = Field(description="Railway environment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class CreateServiceInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    name: str = Field(description="Service name")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    repo: str | None = Field(
        default=None, description="GitHub repository in owner/name format to deploy from"
    )
    image: str | None = Field(
        default=None, description="Docker image to deploy, for example redis:7-alpine"
    )
    branch: str | None = Field(
        default=None, description="Git branch to deploy when using a repository source"
    )


class DeleteServiceInput(BaseModel):
    service_id: str = Field(description="Railway service ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class ListDeploymentsInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    service_id: str = Field(description="Railway service ID")
    environment_id: str = Field(description="Railway environment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    first: int | None = Field(default=None, description="Maximum number of deployments to return")
    after: str | None = Field(default=None, description="Cursor for pagination")


class GetDeploymentInput(BaseModel):
    deployment_id: str = Field(description="Railway deployment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class DeployServiceInput(BaseModel):
    service_id: str = Field(description="Railway service ID")
    environment_id: str = Field(description="Railway environment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    commit_sha: str | None = Field(default=None, description="Specific Git commit SHA to deploy")


class RestartDeploymentInput(BaseModel):
    deployment_id: str = Field(description="Railway deployment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class RollbackDeploymentInput(BaseModel):
    deployment_id: str = Field(
        description="Railway deployment ID to roll back to (must have canRollback)"
    )
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)


class GetDeploymentLogsInput(BaseModel):
    deployment_id: str = Field(description="Railway deployment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    limit: int | None = Field(default=None, description="Maximum number of log lines to return")


class ListVariablesInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    environment_id: str = Field(description="Railway environment ID")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    service_id: str | None = Field(
        default=None, description="Railway service ID. Omit for shared environment variables."
    )


class UpsertVariableInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    environment_id: str = Field(description="Railway environment ID")
    name: str = Field(description="Variable name")
    value: str = Field(description="Variable value")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    service_id: str | None = Field(
        default=None, description="Railway service ID. Omit to create or update a shared variable."
    )
    skip_deploys: bool | None = Field(
        default=None, description="Whether to skip automatic redeploys after changing the variable"
    )


class DeleteVariableInput(BaseModel):
    project_id: str = Field(description="Railway project ID")
    environment_id: str = Field(description="Railway environment ID")
    name: str = Field(description="Variable name to delete")
    api_key: str = Field(description="Railway API token (provided by credential system)")
    token_type: str = Field(default="account", description=_TOKEN_TYPE_DESC)
    service_id: str | None = Field(
        default=None, description="Railway service ID. Omit to delete a shared variable."
    )


# --- @tool functions -------------------------------------------------------


@tool(args_schema=ListProjectsInput)
@serialize_pydantic_return
async def list_projects(
    api_key: str,
    token_type: str = "account",
    workspace_id: str | None = None,
    first: int | None = None,
    after: str | None = None,
) -> ListProjectsOutput:
    """List Railway projects visible to the provided token."""
    if not api_key or not api_key.strip():
        return ListProjectsOutput(success=False, error="Railway API token is empty.")

    query = """
        query ListProjects($workspaceId: String, $first: Int, $after: String) {
          projects(workspaceId: $workspaceId, first: $first, after: $after) {
            edges {
              node {
                id
                name
                description
                createdAt
                updatedAt
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
    """
    variables: dict[str, Any] = {}
    workspace = _optional(workspace_id)
    if workspace is not None:
        variables["workspaceId"] = workspace
    if first is not None:
        variables["first"] = first
    cursor = _optional(after)
    if cursor is not None:
        variables["after"] = cursor

    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return ListProjectsOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return ListProjectsOutput(success=False, error=str(exc))
    except Exception as exc:
        return ListProjectsOutput(success=False, error=f"List projects failed: {exc}")

    connection = data.get("projects") or {}
    edges = connection.get("edges") or []
    projects = [
        ProjectSummary(
            id=node.get("id"),
            name=node.get("name"),
            description=node.get("description"),
            created_at=node.get("createdAt"),
            updated_at=node.get("updatedAt"),
        )
        for node in (edge.get("node") for edge in edges)
        if node
    ]
    page = connection.get("pageInfo") or {}
    return ListProjectsOutput(
        success=True,
        projects=projects,
        page_info=PageInfo(has_next_page=page.get("hasNextPage"), end_cursor=page.get("endCursor")),
        count=len(projects),
    )


@tool(args_schema=GetProjectInput)
@serialize_pydantic_return
async def get_project(
    project_id: str,
    api_key: str,
    token_type: str = "account",
) -> GetProjectOutput:
    """Get a Railway project with its services and environments."""
    if not api_key or not api_key.strip():
        return GetProjectOutput(success=False, error="Railway API token is empty.")

    query = """
        query GetProject($id: String!) {
          project(id: $id) {
            id
            name
            description
            createdAt
            updatedAt
            services {
              edges {
                node {
                  id
                  name
                  icon
                }
              }
            }
            environments {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
    """
    variables: dict[str, Any] = {"id": project_id.strip()}

    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return GetProjectOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return GetProjectOutput(success=False, error=str(exc))
    except Exception as exc:
        return GetProjectOutput(success=False, error=f"Get project failed: {exc}")

    project = data.get("project")
    if not project:
        return GetProjectOutput(success=False, error="Railway did not return a project")

    service_edges = (project.get("services") or {}).get("edges") or []
    services = [
        ProjectService(id=node.get("id"), name=node.get("name"), icon=node.get("icon"))
        for node in (edge.get("node") for edge in service_edges)
        if node
    ]
    env_edges = (project.get("environments") or {}).get("edges") or []
    environments = [
        ProjectEnvironment(id=node.get("id"), name=node.get("name"))
        for node in (edge.get("node") for edge in env_edges)
        if node
    ]
    return GetProjectOutput(
        success=True,
        project=ProjectDetail(
            id=project.get("id"),
            name=project.get("name"),
            description=project.get("description"),
            created_at=project.get("createdAt"),
            updated_at=project.get("updatedAt"),
            services=services,
            environments=environments,
        ),
    )


@tool(args_schema=CreateProjectInput)
@serialize_pydantic_return
async def create_project(
    name: str,
    api_key: str,
    token_type: str = "account",
    description: str | None = None,
    workspace_id: str | None = None,
    is_public: bool | None = None,
    default_environment_name: str | None = None,
    pr_deploys: bool | None = None,
) -> CreateProjectOutput:
    """Create a Railway project."""
    if not api_key or not api_key.strip():
        return CreateProjectOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation CreateProject($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            id
            name
          }
        }
    """
    project_input: dict[str, Any] = {"name": name.strip()}
    description_value = _optional(description)
    if description_value is not None:
        project_input["description"] = description_value
    workspace = _optional(workspace_id)
    if workspace is not None:
        project_input["workspaceId"] = workspace
    if is_public is not None:
        project_input["isPublic"] = is_public
    default_env = _optional(default_environment_name)
    if default_env is not None:
        project_input["defaultEnvironmentName"] = default_env
    if pr_deploys is not None:
        project_input["prDeploys"] = pr_deploys

    try:
        data = await _execute(query, {"input": project_input}, api_key, token_type)
    except httpx.TimeoutException:
        return CreateProjectOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return CreateProjectOutput(success=False, error=str(exc))
    except Exception as exc:
        return CreateProjectOutput(success=False, error=f"Create project failed: {exc}")

    project = data.get("projectCreate")
    if not project:
        return CreateProjectOutput(success=False, error="Railway did not return a created project")
    return CreateProjectOutput(
        success=True,
        project=CreatedResource(id=project.get("id"), name=project.get("name")),
    )


@tool(args_schema=UpdateProjectInput)
@serialize_pydantic_return
async def update_project(
    project_id: str,
    api_key: str,
    token_type: str = "account",
    name: str | None = None,
    description: str | None = None,
    is_public: bool | None = None,
    pr_deploys: bool | None = None,
) -> UpdateProjectOutput:
    """Update a Railway project name or description."""
    if not api_key or not api_key.strip():
        return UpdateProjectOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {
          projectUpdate(id: $id, input: $input) {
            id
            name
            description
          }
        }
    """
    update_input: dict[str, Any] = {}
    name_value = _optional(name)
    if name_value is not None:
        update_input["name"] = name_value
    description_value = _optional(description)
    if description_value is not None:
        update_input["description"] = description_value
    if is_public is not None:
        update_input["isPublic"] = is_public
    if pr_deploys is not None:
        update_input["prDeploys"] = pr_deploys

    variables: dict[str, Any] = {"id": project_id.strip(), "input": update_input}
    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return UpdateProjectOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return UpdateProjectOutput(success=False, error=str(exc))
    except Exception as exc:
        return UpdateProjectOutput(success=False, error=f"Update project failed: {exc}")

    project = data.get("projectUpdate")
    if not project:
        return UpdateProjectOutput(success=False, error="Railway did not return an updated project")
    return UpdateProjectOutput(
        success=True,
        project=UpdatedProject(
            id=project.get("id"),
            name=project.get("name"),
            description=project.get("description"),
        ),
    )


@tool(args_schema=DeleteProjectInput)
@serialize_pydantic_return
async def delete_project(
    project_id: str,
    api_key: str,
    token_type: str = "account",
) -> DeleteProjectOutput:
    """Delete a Railway project."""
    if not api_key or not api_key.strip():
        return DeleteProjectOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation DeleteProject($id: String!) {
          projectDelete(id: $id)
        }
    """
    try:
        data = await _execute(query, {"id": project_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return DeleteProjectOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return DeleteProjectOutput(success=False, error=str(exc))
    except Exception as exc:
        return DeleteProjectOutput(success=False, error=f"Delete project failed: {exc}")

    result = data.get("projectDelete")
    if not isinstance(result, bool):
        return DeleteProjectOutput(
            success=False, error="Railway did not return a project deletion result"
        )
    return DeleteProjectOutput(success=True, deleted=result)


@tool(args_schema=TransferProjectInput)
@serialize_pydantic_return
async def transfer_project(
    project_id: str,
    workspace_id: str,
    api_key: str,
    token_type: str = "account",
) -> TransferProjectOutput:
    """Transfer a Railway project to another workspace."""
    if not api_key or not api_key.strip():
        return TransferProjectOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation TransferProject($projectId: String!, $input: ProjectTransferInput!) {
          projectTransfer(projectId: $projectId, input: $input)
        }
    """
    variables: dict[str, Any] = {
        "projectId": project_id.strip(),
        "input": {"workspaceId": workspace_id.strip()},
    }
    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return TransferProjectOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return TransferProjectOutput(success=False, error=str(exc))
    except Exception as exc:
        return TransferProjectOutput(success=False, error=f"Transfer project failed: {exc}")

    result = data.get("projectTransfer")
    if not isinstance(result, bool):
        return TransferProjectOutput(
            success=False, error="Railway did not return a project transfer result"
        )
    return TransferProjectOutput(success=True, transferred=result)


@tool(args_schema=ListProjectMembersInput)
@serialize_pydantic_return
async def list_project_members(
    project_id: str,
    api_key: str,
    token_type: str = "account",
) -> ListProjectMembersOutput:
    """List members for a Railway project."""
    if not api_key or not api_key.strip():
        return ListProjectMembersOutput(success=False, error="Railway API token is empty.")

    query = """
        query ProjectMembers($projectId: String!) {
          projectMembers(projectId: $projectId) {
            id
            role
            name
            email
            avatar
          }
        }
    """
    try:
        data = await _execute(query, {"projectId": project_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return ListProjectMembersOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return ListProjectMembersOutput(success=False, error=str(exc))
    except Exception as exc:
        return ListProjectMembersOutput(success=False, error=f"List project members failed: {exc}")

    project_members = data.get("projectMembers")
    if project_members is None:
        return ListProjectMembersOutput(
            success=False, error="Railway did not return project members"
        )
    members = [
        ProjectMember(
            id=member.get("id"),
            role=member.get("role"),
            name=member.get("name"),
            email=member.get("email"),
            avatar=member.get("avatar"),
        )
        for member in project_members
    ]
    return ListProjectMembersOutput(success=True, members=members, count=len(members))


@tool(args_schema=CreateEnvironmentInput)
@serialize_pydantic_return
async def create_environment(
    project_id: str,
    name: str,
    api_key: str,
    token_type: str = "account",
    source_environment_id: str | None = None,
    ephemeral: bool | None = None,
    skip_initial_deploys: bool | None = None,
    stage_initial_changes: bool | None = None,
) -> CreateEnvironmentOutput:
    """Create a Railway project environment."""
    if not api_key or not api_key.strip():
        return CreateEnvironmentOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation CreateEnvironment($input: EnvironmentCreateInput!) {
          environmentCreate(input: $input) {
            id
            name
          }
        }
    """
    env_input: dict[str, Any] = {"projectId": project_id.strip(), "name": name.strip()}
    source = _optional(source_environment_id)
    if source is not None:
        env_input["sourceEnvironmentId"] = source
    if ephemeral is not None:
        env_input["ephemeral"] = ephemeral
    if skip_initial_deploys is not None:
        env_input["skipInitialDeploys"] = skip_initial_deploys
    if stage_initial_changes is not None:
        env_input["stageInitialChanges"] = stage_initial_changes

    try:
        data = await _execute(query, {"input": env_input}, api_key, token_type)
    except httpx.TimeoutException:
        return CreateEnvironmentOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return CreateEnvironmentOutput(success=False, error=str(exc))
    except Exception as exc:
        return CreateEnvironmentOutput(success=False, error=f"Create environment failed: {exc}")

    environment = data.get("environmentCreate")
    if not environment:
        return CreateEnvironmentOutput(
            success=False, error="Railway did not return a created environment"
        )
    return CreateEnvironmentOutput(
        success=True,
        environment=CreatedResource(id=environment.get("id"), name=environment.get("name")),
    )


@tool(args_schema=DeleteEnvironmentInput)
@serialize_pydantic_return
async def delete_environment(
    environment_id: str,
    api_key: str,
    token_type: str = "account",
) -> DeleteEnvironmentOutput:
    """Delete a Railway project environment."""
    if not api_key or not api_key.strip():
        return DeleteEnvironmentOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation DeleteEnvironment($id: String!) {
          environmentDelete(id: $id)
        }
    """
    try:
        data = await _execute(query, {"id": environment_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return DeleteEnvironmentOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return DeleteEnvironmentOutput(success=False, error=str(exc))
    except Exception as exc:
        return DeleteEnvironmentOutput(success=False, error=f"Delete environment failed: {exc}")

    result = data.get("environmentDelete")
    if not isinstance(result, bool):
        return DeleteEnvironmentOutput(
            success=False, error="Railway did not return an environment deletion result"
        )
    return DeleteEnvironmentOutput(success=True, deleted=result)


@tool(args_schema=CreateServiceInput)
@serialize_pydantic_return
async def create_service(
    project_id: str,
    name: str,
    api_key: str,
    token_type: str = "account",
    repo: str | None = None,
    image: str | None = None,
    branch: str | None = None,
) -> CreateServiceOutput:
    """Create a Railway service from a GitHub repo or Docker image."""
    if not api_key or not api_key.strip():
        return CreateServiceOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation CreateService($input: ServiceCreateInput!) {
          serviceCreate(input: $input) {
            id
            name
          }
        }
    """
    repo_value = _optional(repo)
    image_value = _optional(image)
    branch_value = _optional(branch)
    service_input: dict[str, Any] = {"projectId": project_id.strip(), "name": name.strip()}
    if repo_value:
        service_input["source"] = {"repo": repo_value}
    elif image_value:
        service_input["source"] = {"image": image_value}
    if branch_value:
        service_input["branch"] = branch_value

    try:
        data = await _execute(query, {"input": service_input}, api_key, token_type)
    except httpx.TimeoutException:
        return CreateServiceOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return CreateServiceOutput(success=False, error=str(exc))
    except Exception as exc:
        return CreateServiceOutput(success=False, error=f"Create service failed: {exc}")

    service = data.get("serviceCreate")
    if not service:
        return CreateServiceOutput(success=False, error="Railway did not return a created service")
    return CreateServiceOutput(
        success=True,
        service=CreatedResource(id=service.get("id"), name=service.get("name")),
    )


@tool(args_schema=DeleteServiceInput)
@serialize_pydantic_return
async def delete_service(
    service_id: str,
    api_key: str,
    token_type: str = "account",
) -> DeleteServiceOutput:
    """Delete a Railway service and all of its deployments."""
    if not api_key or not api_key.strip():
        return DeleteServiceOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation DeleteService($id: String!) {
          serviceDelete(id: $id)
        }
    """
    try:
        data = await _execute(query, {"id": service_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return DeleteServiceOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return DeleteServiceOutput(success=False, error=str(exc))
    except Exception as exc:
        return DeleteServiceOutput(success=False, error=f"Delete service failed: {exc}")

    result = data.get("serviceDelete")
    if not isinstance(result, bool):
        return DeleteServiceOutput(
            success=False, error="Railway did not return a service deletion result"
        )
    return DeleteServiceOutput(success=True, deleted=result)


@tool(args_schema=ListDeploymentsInput)
@serialize_pydantic_return
async def list_deployments(
    project_id: str,
    service_id: str,
    environment_id: str,
    api_key: str,
    token_type: str = "account",
    first: int | None = None,
    after: str | None = None,
) -> ListDeploymentsOutput:
    """List deployments for a Railway service in an environment."""
    if not api_key or not api_key.strip():
        return ListDeploymentsOutput(success=False, error="Railway API token is empty.")

    query = """
        query ListDeployments($input: DeploymentListInput!, $first: Int, $after: String) {
          deployments(input: $input, first: $first, after: $after) {
            edges {
              node {
                id
                status
                createdAt
                url
                staticUrl
                canRollback
                canRedeploy
              }
            }
            pageInfo {
              hasNextPage
              endCursor
            }
          }
        }
    """
    variables: dict[str, Any] = {
        "input": {
            "projectId": project_id.strip(),
            "serviceId": service_id.strip(),
            "environmentId": environment_id.strip(),
        },
        "first": first if first else 10,
    }
    cursor = _optional(after)
    if cursor is not None:
        variables["after"] = cursor

    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return ListDeploymentsOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return ListDeploymentsOutput(success=False, error=str(exc))
    except Exception as exc:
        return ListDeploymentsOutput(success=False, error=f"List deployments failed: {exc}")

    connection = data.get("deployments") or {}
    edges = connection.get("edges") or []
    deployments = [
        DeploymentSummary(
            id=node.get("id"),
            status=node.get("status"),
            created_at=node.get("createdAt"),
            url=node.get("url"),
            static_url=node.get("staticUrl"),
            can_rollback=node.get("canRollback") if node.get("canRollback") is not None else False,
            can_redeploy=node.get("canRedeploy") if node.get("canRedeploy") is not None else False,
        )
        for node in (edge.get("node") for edge in edges)
        if node
    ]
    page = connection.get("pageInfo") or {}
    return ListDeploymentsOutput(
        success=True,
        deployments=deployments,
        page_info=PageInfo(has_next_page=page.get("hasNextPage"), end_cursor=page.get("endCursor")),
        count=len(deployments),
    )


@tool(args_schema=GetDeploymentInput)
@serialize_pydantic_return
async def get_deployment(
    deployment_id: str,
    api_key: str,
    token_type: str = "account",
) -> GetDeploymentOutput:
    """Get details for a single Railway deployment."""
    if not api_key or not api_key.strip():
        return GetDeploymentOutput(success=False, error="Railway API token is empty.")

    query = """
        query GetDeployment($id: String!) {
          deployment(id: $id) {
            id
            status
            createdAt
            url
            staticUrl
            canRollback
            canRedeploy
          }
        }
    """
    try:
        data = await _execute(query, {"id": deployment_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return GetDeploymentOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return GetDeploymentOutput(success=False, error=str(exc))
    except Exception as exc:
        return GetDeploymentOutput(success=False, error=f"Get deployment failed: {exc}")

    deployment = data.get("deployment")
    if not deployment:
        return GetDeploymentOutput(success=False, error="Railway did not return a deployment")
    return GetDeploymentOutput(
        success=True,
        deployment=DeploymentDetail(
            id=deployment.get("id"),
            status=deployment.get("status"),
            created_at=deployment.get("createdAt"),
            url=deployment.get("url"),
            static_url=deployment.get("staticUrl"),
            can_rollback=deployment.get("canRollback")
            if deployment.get("canRollback") is not None
            else False,
            can_redeploy=deployment.get("canRedeploy")
            if deployment.get("canRedeploy") is not None
            else False,
        ),
    )


@tool(args_schema=DeployServiceInput)
@serialize_pydantic_return
async def deploy_service(
    service_id: str,
    environment_id: str,
    api_key: str,
    token_type: str = "account",
    commit_sha: str | None = None,
) -> DeployServiceOutput:
    """Trigger a deployment for a Railway service in an environment."""
    if not api_key or not api_key.strip():
        return DeployServiceOutput(success=False, error="Railway API token is empty.")

    commit = _optional(commit_sha)
    if commit:
        query = """
            mutation DeployService(
              $serviceId: String!
              $environmentId: String!
              $commitSha: String!
            ) {
              serviceInstanceDeployV2(
                serviceId: $serviceId
                environmentId: $environmentId
                commitSha: $commitSha
              )
            }
        """
        variables: dict[str, Any] = {
            "serviceId": service_id.strip(),
            "environmentId": environment_id.strip(),
            "commitSha": commit,
        }
    else:
        query = """
            mutation DeployService($serviceId: String!, $environmentId: String!) {
              serviceInstanceDeployV2(serviceId: $serviceId, environmentId: $environmentId)
            }
        """
        variables = {
            "serviceId": service_id.strip(),
            "environmentId": environment_id.strip(),
        }

    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return DeployServiceOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return DeployServiceOutput(success=False, error=str(exc))
    except Exception as exc:
        return DeployServiceOutput(success=False, error=f"Deploy service failed: {exc}")

    deployment_id = data.get("serviceInstanceDeployV2")
    if not deployment_id:
        return DeployServiceOutput(success=False, error="Railway did not return a deployment ID")
    return DeployServiceOutput(success=True, deployment_id=deployment_id)


@tool(args_schema=RestartDeploymentInput)
@serialize_pydantic_return
async def restart_deployment(
    deployment_id: str,
    api_key: str,
    token_type: str = "account",
) -> RestartDeploymentOutput:
    """Restart a running Railway deployment without rebuilding."""
    if not api_key or not api_key.strip():
        return RestartDeploymentOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation RestartDeployment($id: String!) {
          deploymentRestart(id: $id)
        }
    """
    try:
        data = await _execute(query, {"id": deployment_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return RestartDeploymentOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return RestartDeploymentOutput(success=False, error=str(exc))
    except Exception as exc:
        return RestartDeploymentOutput(success=False, error=f"Restart deployment failed: {exc}")

    result = data.get("deploymentRestart")
    if not isinstance(result, bool):
        return RestartDeploymentOutput(
            success=False, error="Railway did not return a deployment restart result"
        )
    return RestartDeploymentOutput(success=True, restarted=result)


@tool(args_schema=RollbackDeploymentInput)
@serialize_pydantic_return
async def rollback_deployment(
    deployment_id: str,
    api_key: str,
    token_type: str = "account",
) -> RollbackDeploymentOutput:
    """Roll a Railway service back to a previous deployment."""
    if not api_key or not api_key.strip():
        return RollbackDeploymentOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation RollbackDeployment($id: String!) {
          deploymentRollback(id: $id)
        }
    """
    try:
        data = await _execute(query, {"id": deployment_id.strip()}, api_key, token_type)
    except httpx.TimeoutException:
        return RollbackDeploymentOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return RollbackDeploymentOutput(success=False, error=str(exc))
    except Exception as exc:
        return RollbackDeploymentOutput(success=False, error=f"Rollback deployment failed: {exc}")

    result = data.get("deploymentRollback")
    if not isinstance(result, bool):
        return RollbackDeploymentOutput(
            success=False, error="Railway did not return a rollback result"
        )
    return RollbackDeploymentOutput(success=True, rolled_back=result)


@tool(args_schema=GetDeploymentLogsInput)
@serialize_pydantic_return
async def get_deployment_logs(
    deployment_id: str,
    api_key: str,
    token_type: str = "account",
    limit: int | None = None,
) -> GetDeploymentLogsOutput:
    """Retrieve runtime logs for a Railway deployment."""
    if not api_key or not api_key.strip():
        return GetDeploymentLogsOutput(success=False, error="Railway API token is empty.")

    query = """
        query DeploymentLogs($deploymentId: String!, $limit: Int) {
          deploymentLogs(deploymentId: $deploymentId, limit: $limit) {
            timestamp
            message
            severity
          }
        }
    """
    variables: dict[str, Any] = {"deploymentId": deployment_id.strip()}
    if limit is not None:
        variables["limit"] = limit

    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return GetDeploymentLogsOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return GetDeploymentLogsOutput(success=False, error=str(exc))
    except Exception as exc:
        return GetDeploymentLogsOutput(success=False, error=f"Get deployment logs failed: {exc}")

    log_entries = data.get("deploymentLogs")
    if log_entries is None:
        return GetDeploymentLogsOutput(
            success=False, error="Railway did not return deployment logs"
        )
    logs = [
        DeploymentLog(
            timestamp=entry.get("timestamp"),
            message=entry.get("message"),
            severity=entry.get("severity"),
        )
        for entry in log_entries
    ]
    return GetDeploymentLogsOutput(success=True, logs=logs, count=len(logs))


@tool(args_schema=ListVariablesInput)
@serialize_pydantic_return
async def list_variables(
    project_id: str,
    environment_id: str,
    api_key: str,
    token_type: str = "account",
    service_id: str | None = None,
) -> ListVariablesOutput:
    """List Railway environment variables for a service or shared environment."""
    if not api_key or not api_key.strip():
        return ListVariablesOutput(success=False, error="Railway API token is empty.")

    query = """
        query Variables($projectId: String!, $environmentId: String!, $serviceId: String) {
          variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId)
        }
    """
    variables: dict[str, Any] = {
        "projectId": project_id.strip(),
        "environmentId": environment_id.strip(),
    }
    service = _optional(service_id)
    if service is not None:
        variables["serviceId"] = service

    try:
        data = await _execute(query, variables, api_key, token_type)
    except httpx.TimeoutException:
        return ListVariablesOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return ListVariablesOutput(success=False, error=str(exc))
    except Exception as exc:
        return ListVariablesOutput(success=False, error=f"List variables failed: {exc}")

    result = data.get("variables")
    if result is None:
        return ListVariablesOutput(success=False, error="Railway did not return variables")
    return ListVariablesOutput(success=True, variables=result, count=len(result))


@tool(args_schema=UpsertVariableInput)
@serialize_pydantic_return
async def upsert_variable(
    project_id: str,
    environment_id: str,
    name: str,
    value: str,
    api_key: str,
    token_type: str = "account",
    service_id: str | None = None,
    skip_deploys: bool | None = None,
) -> UpsertVariableOutput:
    """Create or update a Railway environment variable."""
    if not api_key or not api_key.strip():
        return UpsertVariableOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation UpsertVariable($input: VariableUpsertInput!) {
          variableUpsert(input: $input)
        }
    """
    variable_input: dict[str, Any] = {
        "projectId": project_id.strip(),
        "environmentId": environment_id.strip(),
        "name": name.strip(),
        "value": value,
    }
    service = _optional(service_id)
    if service is not None:
        variable_input["serviceId"] = service
    if skip_deploys is not None:
        variable_input["skipDeploys"] = skip_deploys

    try:
        data = await _execute(query, {"input": variable_input}, api_key, token_type)
    except httpx.TimeoutException:
        return UpsertVariableOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return UpsertVariableOutput(success=False, error=str(exc))
    except Exception as exc:
        return UpsertVariableOutput(success=False, error=f"Upsert variable failed: {exc}")

    result = data.get("variableUpsert")
    if not isinstance(result, bool):
        return UpsertVariableOutput(
            success=False, error="Railway did not return a variable upsert result"
        )
    return UpsertVariableOutput(success=True, upserted=result)


@tool(args_schema=DeleteVariableInput)
@serialize_pydantic_return
async def delete_variable(
    project_id: str,
    environment_id: str,
    name: str,
    api_key: str,
    token_type: str = "account",
    service_id: str | None = None,
) -> DeleteVariableOutput:
    """Delete a Railway environment variable."""
    if not api_key or not api_key.strip():
        return DeleteVariableOutput(success=False, error="Railway API token is empty.")

    query = """
        mutation DeleteVariable($input: VariableDeleteInput!) {
          variableDelete(input: $input)
        }
    """
    variable_input: dict[str, Any] = {
        "projectId": project_id.strip(),
        "environmentId": environment_id.strip(),
        "name": name.strip(),
    }
    service = _optional(service_id)
    if service is not None:
        variable_input["serviceId"] = service

    try:
        data = await _execute(query, {"input": variable_input}, api_key, token_type)
    except httpx.TimeoutException:
        return DeleteVariableOutput(success=False, error="Request timed out.")
    except _GraphqlError as exc:
        return DeleteVariableOutput(success=False, error=str(exc))
    except Exception as exc:
        return DeleteVariableOutput(success=False, error=f"Delete variable failed: {exc}")

    result = data.get("variableDelete")
    if not isinstance(result, bool):
        return DeleteVariableOutput(
            success=False, error="Railway did not return a variable deletion result"
        )
    return DeleteVariableOutput(success=True, deleted=result)
