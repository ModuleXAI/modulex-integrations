"""Pydantic response models for the Vercel integration's @tool functions.

The Vercel REST API returns proper HTTP status codes; every tool wraps
its call in try/except so non-2xx responses and timeouts surface as
``success=False`` + ``error`` rather than raising. Each output model
therefore carries both shapes: a ``success`` flag, an optional
``error`` string, and data fields that stay at their permissive
defaults on the failure branch.

Fields are deliberately permissive (``<type> | None = None`` for
scalars, ``Field(default_factory=list)`` for collections) because the
upstream API is read with ``.get()`` everywhere and routinely omits
optional keys.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "AddDomainOutput",
    "AddProjectDomainOutput",
    "AliasItem",
    "CancelDeploymentOutput",
    "CheckItem",
    "CheckOutput",
    "CreateAliasOutput",
    "CreateDeploymentOutput",
    "CreateDnsRecordOutput",
    "CreateEdgeConfigOutput",
    "CreateEnvVarOutput",
    "CreateProjectOutput",
    "CreateWebhookOutput",
    "DeleteAliasOutput",
    "DeleteDeploymentOutput",
    "DeleteDnsRecordOutput",
    "DeleteDomainOutput",
    "DeleteEdgeConfigOutput",
    "DeleteEnvVarOutput",
    "DeleteProjectOutput",
    "DeleteWebhookOutput",
    "DeploymentCreator",
    "DeploymentEvent",
    "DeploymentFile",
    "DeploymentItem",
    "DnsRecordItem",
    "DomainConfigCnameRecommendation",
    "DomainConfigIpv4Recommendation",
    "DomainCreator",
    "DomainItem",
    "DomainVerification",
    "EdgeConfigItem",
    "EdgeConfigStore",
    "EnvVarItem",
    "GetAliasOutput",
    "GetCheckOutput",
    "GetDeploymentEventsOutput",
    "GetDeploymentOutput",
    "GetDomainConfigOutput",
    "GetDomainOutput",
    "GetEdgeConfigItemsOutput",
    "GetEdgeConfigOutput",
    "GetEnvVarsOutput",
    "GetProjectOutput",
    "GetTeamOutput",
    "GetUserOutput",
    "GetWebhookOutput",
    "ListAliasesOutput",
    "ListChecksOutput",
    "ListDeploymentFilesOutput",
    "ListDeploymentsOutput",
    "ListDnsRecordsOutput",
    "ListDomainsOutput",
    "ListEdgeConfigsOutput",
    "ListProjectDomainsOutput",
    "ListProjectsOutput",
    "ListTeamMembersOutput",
    "ListTeamsOutput",
    "ListWebhooksOutput",
    "PauseProjectOutput",
    "ProjectDomainItem",
    "ProjectItem",
    "ProjectLink",
    "PromoteDeploymentOutput",
    "RemoveProjectDomainOutput",
    "RerequestCheckOutput",
    "TeamItem",
    "TeamMember",
    "UnpauseProjectOutput",
    "UpdateCheckOutput",
    "UpdateDnsRecordOutput",
    "UpdateEdgeConfigItemsOutput",
    "UpdateEnvVarOutput",
    "UpdateProjectDomainOutput",
    "UpdateProjectOutput",
    "VerifyProjectDomainOutput",
    "WebhookItem",
]


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --- Shared nested resource models -----------------------------------------


class DeploymentCreator(_Base):
    uid: str | None = None
    email: str | None = None
    username: str | None = None


class DomainCreator(_Base):
    id: str | None = None
    username: str | None = None
    email: str | None = None


class DomainVerification(_Base):
    type: str | None = None
    domain: str | None = None
    value: str | None = None
    reason: str | None = None


class ProjectLink(_Base):
    type: str | None = None
    repo: str | None = None
    org: str | None = None


class DeploymentItem(_Base):
    uid: str | None = None
    name: str | None = None
    url: str | None = None
    state: str | None = None
    target: str | None = None
    created: int | None = None
    project_id: str | None = None
    source: str | None = None
    inspector_url: str | None = None
    checks_state: str | None = None
    checks_conclusion: str | None = None
    error_message: str | None = None
    creator: DeploymentCreator | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ProjectItem(_Base):
    id: str | None = None
    name: str | None = None
    framework: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class DomainItem(_Base):
    id: str | None = None
    name: str | None = None
    verified: bool | None = None
    created_at: int | None = None
    expires_at: int | None = None
    service_type: str | None = None
    nameservers: list[str] = Field(default_factory=list)
    intended_nameservers: list[str] = Field(default_factory=list)
    renew: bool | None = None
    bought_at: int | None = None
    transferred_at: int | None = None
    creator: DomainCreator | None = None


class EnvVarItem(_Base):
    id: str | None = None
    key: str | None = None
    value: str | None = None
    type: str | None = None
    target: list[str] = Field(default_factory=list)
    git_branch: str | None = None
    comment: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class DeploymentEvent(_Base):
    type: str | None = None
    created: int | None = None
    date: int | None = None
    text: str | None = None
    serial: str | None = None
    deployment_id: str | None = None
    id: str | None = None
    level: str | None = None
    info: dict[str, Any] | None = None


class DeploymentFile(_Base):
    name: str | None = None
    type: str | None = None
    uid: str | None = None
    mode: int | None = None
    content_type: str | None = None
    children: list[Any] = Field(default_factory=list)


class ProjectDomainItem(_Base):
    name: str | None = None
    apex_name: str | None = None
    redirect: str | None = None
    redirect_status_code: int | None = None
    verified: bool | None = None
    git_branch: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    project_id: str | None = None
    verification: list[DomainVerification] = Field(default_factory=list)


class DnsRecordItem(_Base):
    id: str | None = None
    slug: str | None = None
    name: str | None = None
    type: str | None = None
    value: str | None = None
    ttl: int | None = None
    mx_priority: int | None = None
    priority: int | None = None
    creator: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    comment: str | None = None


class AliasItem(_Base):
    uid: str | None = None
    alias: str | None = None
    deployment_id: str | None = None
    project_id: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    deployment: dict[str, Any] | None = None
    redirect: str | None = None
    redirect_status_code: int | None = None


class EdgeConfigStore(_Base):
    id: str | None = None
    slug: str | None = None
    owner_id: str | None = None
    digest: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    item_count: int | None = None
    size_in_bytes: int | None = None


class EdgeConfigItem(_Base):
    key: str | None = None
    value: Any = None
    description: str | None = None
    edge_config_id: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class TeamItem(_Base):
    id: str | None = None
    slug: str | None = None
    name: str | None = None
    avatar: str | None = None
    description: str | None = None
    staging_prefix: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    creator_id: str | None = None
    membership: dict[str, Any] | None = None


class TeamMember(_Base):
    uid: str | None = None
    email: str | None = None
    username: str | None = None
    name: str | None = None
    avatar: str | None = None
    role: str | None = None
    confirmed: bool | None = None
    created_at: int | None = None
    access_requested_at: int | None = None
    is_enterprise_managed: bool | None = None
    joined_from: dict[str, Any] | None = None


class WebhookItem(_Base):
    id: str | None = None
    url: str | None = None
    events: list[str] = Field(default_factory=list)
    owner_id: str | None = None
    project_ids: list[str] = Field(default_factory=list)
    projects_metadata: list[Any] = Field(default_factory=list)
    created_at: int | None = None
    updated_at: int | None = None


class CheckItem(_Base):
    id: str | None = None
    name: str | None = None
    status: str | None = None
    conclusion: str | None = None
    blocking: bool | None = None
    deployment_id: str | None = None
    integration_id: str | None = None
    external_id: str | None = None
    details_url: str | None = None
    path: str | None = None
    rerequestable: bool | None = None
    created_at: int | None = None
    updated_at: int | None = None
    started_at: int | None = None
    completed_at: int | None = None
    output: Any = None


class DomainConfigIpv4Recommendation(_Base):
    rank: int | None = None
    value: list[str] = Field(default_factory=list)


class DomainConfigCnameRecommendation(_Base):
    rank: int | None = None
    value: str | None = None


# --- Per-action output models ----------------------------------------------


class ListDeploymentsOutput(_Base):
    success: bool
    error: str | None = None
    deployments: list[DeploymentItem] = Field(default_factory=list)
    count: int = 0
    has_more: bool | None = None


class GetDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    url: str | None = None
    ready_state: str | None = None
    status: str | None = None
    target: str | None = None
    created_at: int | None = None
    building_at: int | None = None
    ready: int | None = None
    source: str | None = None
    alias: list[str] = Field(default_factory=list)
    regions: list[str] = Field(default_factory=list)
    inspector_url: str | None = None
    project_id: str | None = None
    creator: dict[str, Any] | None = None
    project: dict[str, Any] | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    git_source: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    alias_assigned: bool | None = None


class CreateDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    url: str | None = None
    ready_state: str | None = None
    project_id: str | None = None
    created_at: int | None = None
    alias: list[str] = Field(default_factory=list)
    target: str | None = None
    inspector_url: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    alias_assigned: bool | None = None


class CancelDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    state: str | None = None
    url: str | None = None
    status: str | None = None
    project_id: str | None = None
    inspector_url: str | None = None


class DeleteDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    state: str | None = None


class GetDeploymentEventsOutput(_Base):
    success: bool
    error: str | None = None
    events: list[DeploymentEvent] = Field(default_factory=list)
    count: int = 0


class ListDeploymentFilesOutput(_Base):
    success: bool
    error: str | None = None
    files: list[DeploymentFile] = Field(default_factory=list)
    count: int = 0


class PromoteDeploymentOutput(_Base):
    success: bool
    error: str | None = None
    promoted: bool | None = None


class ListProjectsOutput(_Base):
    success: bool
    error: str | None = None
    projects: list[ProjectItem] = Field(default_factory=list)
    count: int = 0
    has_more: bool | None = None


class GetProjectOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    framework: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    link: ProjectLink | None = None


class CreateProjectOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    framework: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class UpdateProjectOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    framework: str | None = None
    updated_at: int | None = None


class DeleteProjectOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class PauseProjectOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    paused: bool | None = None


class UnpauseProjectOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    paused: bool | None = None


class ListProjectDomainsOutput(_Base):
    success: bool
    error: str | None = None
    domains: list[ProjectDomainItem] = Field(default_factory=list)
    count: int = 0
    has_more: bool | None = None


class AddProjectDomainOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    apex_name: str | None = None
    project_id: str | None = None
    verified: bool | None = None
    git_branch: str | None = None
    redirect: str | None = None
    redirect_status_code: int | None = None
    verification: list[DomainVerification] = Field(default_factory=list)
    created_at: int | None = None
    updated_at: int | None = None


class UpdateProjectDomainOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    apex_name: str | None = None
    project_id: str | None = None
    verified: bool | None = None
    redirect: str | None = None
    redirect_status_code: int | None = None
    git_branch: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    verification: list[DomainVerification] = Field(default_factory=list)


class VerifyProjectDomainOutput(_Base):
    success: bool
    error: str | None = None
    name: str | None = None
    apex_name: str | None = None
    project_id: str | None = None
    verified: bool | None = None
    redirect: str | None = None
    redirect_status_code: int | None = None
    git_branch: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class RemoveProjectDomainOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class GetEnvVarsOutput(_Base):
    success: bool
    error: str | None = None
    envs: list[EnvVarItem] = Field(default_factory=list)
    count: int = 0


class CreateEnvVarOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    key: str | None = None
    value: str | None = None
    type: str | None = None
    target: list[str] = Field(default_factory=list)
    git_branch: str | None = None
    comment: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class UpdateEnvVarOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    key: str | None = None
    value: str | None = None
    type: str | None = None
    target: list[str] = Field(default_factory=list)
    git_branch: str | None = None
    comment: str | None = None
    created_at: int | None = None
    updated_at: int | None = None


class DeleteEnvVarOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class ListDomainsOutput(_Base):
    success: bool
    error: str | None = None
    domains: list[DomainItem] = Field(default_factory=list)
    count: int = 0
    has_more: bool | None = None


class GetDomainOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    verified: bool | None = None
    created_at: int | None = None
    expires_at: int | None = None
    service_type: str | None = None
    nameservers: list[str] = Field(default_factory=list)
    intended_nameservers: list[str] = Field(default_factory=list)
    custom_nameservers: list[str] = Field(default_factory=list)
    renew: bool | None = None
    bought_at: int | None = None
    transferred_at: int | None = None
    creator: DomainCreator | None = None
    user_id: str | None = None
    team_id: str | None = None
    transfer_started_at: int | None = None


class AddDomainOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    verified: bool | None = None
    created_at: int | None = None
    service_type: str | None = None
    nameservers: list[str] = Field(default_factory=list)
    intended_nameservers: list[str] = Field(default_factory=list)
    expires_at: int | None = None
    custom_nameservers: list[str] = Field(default_factory=list)
    renew: bool | None = None
    bought_at: int | None = None
    transferred_at: int | None = None
    creator: DomainCreator | None = None


class DeleteDomainOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    deleted: bool | None = None


class GetDomainConfigOutput(_Base):
    success: bool
    error: str | None = None
    configured_by: str | None = None
    accepted_challenges: list[str] = Field(default_factory=list)
    misconfigured: bool | None = None
    recommended_ipv4: list[DomainConfigIpv4Recommendation] = Field(default_factory=list)
    recommended_cname: list[DomainConfigCnameRecommendation] = Field(default_factory=list)


class ListDnsRecordsOutput(_Base):
    success: bool
    error: str | None = None
    records: list[DnsRecordItem] = Field(default_factory=list)
    count: int = 0
    has_more: bool | None = None


class CreateDnsRecordOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    updated: int | None = None


class UpdateDnsRecordOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    type: str | None = None
    value: str | None = None
    creator: str | None = None
    domain: str | None = None
    ttl: int | None = None
    comment: str | None = None
    record_type: str | None = None
    created_at: int | None = None


class DeleteDnsRecordOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class ListAliasesOutput(_Base):
    success: bool
    error: str | None = None
    aliases: list[AliasItem] = Field(default_factory=list)
    count: int = 0
    has_more: bool | None = None


class GetAliasOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    alias: str | None = None
    deployment_id: str | None = None
    project_id: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    redirect: str | None = None
    redirect_status_code: int | None = None
    deployment: dict[str, Any] | None = None


class CreateAliasOutput(_Base):
    success: bool
    error: str | None = None
    uid: str | None = None
    alias: str | None = None
    created: str | None = None
    old_deployment_id: str | None = None


class DeleteAliasOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None


class ListEdgeConfigsOutput(_Base):
    success: bool
    error: str | None = None
    edge_configs: list[EdgeConfigStore] = Field(default_factory=list)
    count: int = 0


class GetEdgeConfigOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    slug: str | None = None
    owner_id: str | None = None
    digest: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    item_count: int | None = None
    size_in_bytes: int | None = None


class CreateEdgeConfigOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    slug: str | None = None
    owner_id: str | None = None
    digest: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    item_count: int | None = None
    size_in_bytes: int | None = None


class DeleteEdgeConfigOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class GetEdgeConfigItemsOutput(_Base):
    success: bool
    error: str | None = None
    items: list[EdgeConfigItem] = Field(default_factory=list)
    count: int = 0


class UpdateEdgeConfigItemsOutput(_Base):
    success: bool
    error: str | None = None
    status: str | None = None


class ListTeamsOutput(_Base):
    success: bool
    error: str | None = None
    teams: list[TeamItem] = Field(default_factory=list)
    count: int = 0
    pagination: dict[str, Any] | None = None


class GetTeamOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    slug: str | None = None
    name: str | None = None
    avatar: str | None = None
    description: str | None = None
    staging_prefix: str | None = None
    created_at: int | None = None
    updated_at: int | None = None
    creator_id: str | None = None
    membership: dict[str, Any] | None = None


class ListTeamMembersOutput(_Base):
    success: bool
    error: str | None = None
    members: list[TeamMember] = Field(default_factory=list)
    count: int = 0
    pagination: dict[str, Any] | None = None


class GetUserOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    email: str | None = None
    username: str | None = None
    name: str | None = None
    avatar: str | None = None
    default_team_id: str | None = None
    created_at: int | None = None
    staging_prefix: str | None = None
    soft_block: dict[str, Any] | None = None
    has_trial_available: bool | None = None


class ListWebhooksOutput(_Base):
    success: bool
    error: str | None = None
    webhooks: list[WebhookItem] = Field(default_factory=list)
    count: int = 0


class GetWebhookOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    url: str | None = None
    events: list[str] = Field(default_factory=list)
    owner_id: str | None = None
    project_ids: list[str] = Field(default_factory=list)
    created_at: int | None = None
    updated_at: int | None = None


class CreateWebhookOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    url: str | None = None
    secret: str | None = None
    events: list[str] = Field(default_factory=list)
    owner_id: str | None = None
    project_ids: list[str] = Field(default_factory=list)
    created_at: int | None = None
    updated_at: int | None = None


class DeleteWebhookOutput(_Base):
    success: bool
    error: str | None = None
    deleted: bool | None = None


class CheckOutput(_Base):
    success: bool
    error: str | None = None
    id: str | None = None
    name: str | None = None
    status: str | None = None
    conclusion: str | None = None
    blocking: bool | None = None
    deployment_id: str | None = None
    integration_id: str | None = None
    external_id: str | None = None
    details_url: str | None = None
    path: str | None = None
    rerequestable: bool | None = None
    created_at: int | None = None
    updated_at: int | None = None
    started_at: int | None = None
    completed_at: int | None = None
    output: Any = None


class GetCheckOutput(CheckOutput):
    pass


class UpdateCheckOutput(CheckOutput):
    pass


class ListChecksOutput(_Base):
    success: bool
    error: str | None = None
    checks: list[CheckItem] = Field(default_factory=list)
    count: int = 0


class RerequestCheckOutput(_Base):
    success: bool
    error: str | None = None
    rerequested: bool | None = None
