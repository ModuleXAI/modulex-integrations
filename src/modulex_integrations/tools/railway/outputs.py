"""Pydantic response models for the Railway integration's @tool functions.

Railway's tools follow the modulex *api_key* runtime convention: the
function signature takes ``api_key: str`` directly (instead of the
``auth_type``/``auth_data`` pair), and the modulex ``ToolExecutor``
injects it from the resolved ``api_key`` credential.

Every model carries ``success: bool`` + ``error: str | None``. Railway's
GraphQL API answers HTTP 200 even for logical errors (it reports them in
a top-level ``errors`` array), so the tools surface those as
``success=False`` + ``error`` rather than raising. Data fields stay
permissive (``| None`` scalars, ``default_factory=list`` collections).
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "CreateEnvironmentOutput",
    "CreateProjectOutput",
    "CreateServiceOutput",
    "CreatedResource",
    "DeleteEnvironmentOutput",
    "DeleteProjectOutput",
    "DeleteServiceOutput",
    "DeleteVariableOutput",
    "DeployServiceOutput",
    "DeploymentDetail",
    "DeploymentLog",
    "DeploymentSummary",
    "GetDeploymentLogsOutput",
    "GetDeploymentOutput",
    "GetProjectOutput",
    "ListDeploymentsOutput",
    "ListProjectMembersOutput",
    "ListProjectsOutput",
    "ListVariablesOutput",
    "PageInfo",
    "ProjectDetail",
    "ProjectEnvironment",
    "ProjectMember",
    "ProjectService",
    "ProjectSummary",
    "RestartDeploymentOutput",
    "RollbackDeploymentOutput",
    "TransferProjectOutput",
    "UpdateProjectOutput",
    "UpdatedProject",
    "UpsertVariableOutput",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Nested resource models ------------------------------------------------


class PageInfo(_Base):
    """Cursor-pagination metadata returned by list actions."""

    has_next_page: bool | None = None
    end_cursor: str | None = None


class ProjectSummary(_Base):
    """A single project row in ``list_projects``."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


class ProjectService(_Base):
    """A service attached to a project in ``get_project``."""

    id: str | None = None
    name: str | None = None
    icon: str | None = None


class ProjectEnvironment(_Base):
    """An environment attached to a project in ``get_project``."""

    id: str | None = None
    name: str | None = None


class ProjectDetail(_Base):
    """A project with its services and environments (``get_project``)."""

    id: str | None = None
    name: str | None = None
    description: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    services: list[ProjectService] = Field(default_factory=list)
    environments: list[ProjectEnvironment] = Field(default_factory=list)


class CreatedResource(_Base):
    """A freshly created resource carrying just id + name."""

    id: str | None = None
    name: str | None = None


class UpdatedProject(_Base):
    """The project echoed back by ``update_project``."""

    id: str | None = None
    name: str | None = None
    description: str | None = None


class ProjectMember(_Base):
    """A single member row in ``list_project_members``."""

    id: str | None = None
    role: str | None = None
    name: str | None = None
    email: str | None = None
    avatar: str | None = None


class DeploymentSummary(_Base):
    """A single deployment row in ``list_deployments``."""

    id: str | None = None
    status: str | None = None
    created_at: str | None = None
    url: str | None = None
    static_url: str | None = None
    can_rollback: bool | None = None
    can_redeploy: bool | None = None


class DeploymentDetail(_Base):
    """The deployment detail returned by ``get_deployment``."""

    id: str | None = None
    status: str | None = None
    created_at: str | None = None
    url: str | None = None
    static_url: str | None = None
    can_rollback: bool | None = None
    can_redeploy: bool | None = None


class DeploymentLog(_Base):
    """A single log entry in ``get_deployment_logs``."""

    timestamp: str | None = None
    message: str | None = None
    severity: str | None = None


# --- Per-action output models ----------------------------------------------


class ListProjectsOutput(_Base):
    success: bool
    error: str | None = None
    projects: list[ProjectSummary] = Field(default_factory=list)
    page_info: PageInfo | None = None
    count: int = 0


class GetProjectOutput(_Base):
    success: bool
    error: str | None = None
    project: ProjectDetail | None = None


class CreateProjectOutput(_Base):
    success: bool
    error: str | None = None
    project: CreatedResource | None = None


class UpdateProjectOutput(_Base):
    success: bool
    error: str | None = None
    project: UpdatedProject | None = None


class DeleteProjectOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class TransferProjectOutput(_Base):
    success: bool
    error: str | None = None
    transferred: bool | None = None


class ListProjectMembersOutput(_Base):
    success: bool
    error: str | None = None
    members: list[ProjectMember] = Field(default_factory=list)
    count: int = 0


class CreateEnvironmentOutput(_Base):
    success: bool
    error: str | None = None
    environment: CreatedResource | None = None


class DeleteEnvironmentOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class CreateServiceOutput(_Base):
    success: bool
    error: str | None = None
    service: CreatedResource | None = None


class DeleteServiceOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class ListDeploymentsOutput(_Base):
    success: bool
    error: str | None = None
    deployments: list[DeploymentSummary] = Field(default_factory=list)
    page_info: PageInfo | None = None
    count: int = 0


class GetDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    deployment: DeploymentDetail | None = None


class DeployServiceOutput(_Base):
    success: bool
    error: str | None = None
    deployment_id: str | None = None


class RestartDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    restarted: bool | None = None


class RollbackDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    rolled_back: bool | None = None


class GetDeploymentLogsOutput(_Base):
    success: bool
    error: str | None = None
    logs: list[DeploymentLog] = Field(default_factory=list)
    count: int = 0


class ListVariablesOutput(_Base):
    success: bool
    error: str | None = None
    variables: dict[str, Any] = Field(default_factory=dict)
    count: int = 0


class UpsertVariableOutput(_Base):
    success: bool
    error: str | None = None
    upserted: bool | None = None


class DeleteVariableOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None
