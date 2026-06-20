"""Vercel LangChain ``@tool`` functions.

Fifty-six async tools wrapping the Vercel REST API
(``https://api.vercel.com``). The calling convention is **key-based**:
the modulex ``ToolExecutor`` injects an ``api_key: str`` directly
(resolved from the user's ``api_key`` credential), not an
``auth_type``/``auth_data`` pair. The key is sent as
``Authorization: Bearer <api_key>``.

Each Vercel endpoint pins its own API version in the path (e.g.
``/v13/deployments``, ``/v9/projects``, ``/v2/teams``,
``/v1/edge-config``); those versions are preserved verbatim.
``teamId`` is an optional query parameter accepted by most endpoints to
scope the request to a team.

Error model: every call is wrapped in try/except so non-2xx responses
and timeouts surface as ``success=False`` + ``error`` rather than
raising.
"""
from __future__ import annotations

from typing import Any

import httpx
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from modulex_integrations import serialize_pydantic_return
from modulex_integrations.tools.vercel.outputs import (
    AddDomainOutput,
    AddProjectDomainOutput,
    AliasItem,
    CancelDeploymentOutput,
    CheckItem,
    CheckOutput,
    CreateAliasOutput,
    CreateDeploymentOutput,
    CreateDnsRecordOutput,
    CreateEdgeConfigOutput,
    CreateEnvVarOutput,
    CreateProjectOutput,
    CreateWebhookOutput,
    DeleteAliasOutput,
    DeleteDeploymentOutput,
    DeleteDnsRecordOutput,
    DeleteDomainOutput,
    DeleteEdgeConfigOutput,
    DeleteEnvVarOutput,
    DeleteProjectOutput,
    DeleteWebhookOutput,
    DeploymentEvent,
    DeploymentFile,
    DeploymentItem,
    DnsRecordItem,
    DomainItem,
    EdgeConfigItem,
    EdgeConfigStore,
    EnvVarItem,
    GetAliasOutput,
    GetCheckOutput,
    GetDeploymentEventsOutput,
    GetDeploymentOutput,
    GetDomainConfigOutput,
    GetDomainOutput,
    GetEdgeConfigItemsOutput,
    GetEdgeConfigOutput,
    GetEnvVarsOutput,
    GetProjectOutput,
    GetTeamOutput,
    GetUserOutput,
    GetWebhookOutput,
    ListAliasesOutput,
    ListChecksOutput,
    ListDeploymentFilesOutput,
    ListDeploymentsOutput,
    ListDnsRecordsOutput,
    ListDomainsOutput,
    ListEdgeConfigsOutput,
    ListProjectDomainsOutput,
    ListProjectsOutput,
    ListTeamMembersOutput,
    ListTeamsOutput,
    ListWebhooksOutput,
    PauseProjectOutput,
    ProjectDomainItem,
    ProjectItem,
    PromoteDeploymentOutput,
    RemoveProjectDomainOutput,
    RerequestCheckOutput,
    TeamItem,
    TeamMember,
    UnpauseProjectOutput,
    UpdateCheckOutput,
    UpdateDnsRecordOutput,
    UpdateEdgeConfigItemsOutput,
    UpdateEnvVarOutput,
    UpdateProjectDomainOutput,
    UpdateProjectOutput,
    VerifyProjectDomainOutput,
    WebhookItem,
)

__all__ = [
    "add_domain",
    "add_project_domain",
    "cancel_deployment",
    "create_alias",
    "create_check",
    "create_deployment",
    "create_dns_record",
    "create_edge_config",
    "create_env_var",
    "create_project",
    "create_webhook",
    "delete_alias",
    "delete_deployment",
    "delete_dns_record",
    "delete_domain",
    "delete_edge_config",
    "delete_env_var",
    "delete_project",
    "delete_webhook",
    "get_alias",
    "get_check",
    "get_deployment",
    "get_deployment_events",
    "get_domain",
    "get_domain_config",
    "get_edge_config",
    "get_edge_config_items",
    "get_env_vars",
    "get_project",
    "get_team",
    "get_user",
    "get_webhook",
    "list_aliases",
    "list_checks",
    "list_deployment_files",
    "list_deployments",
    "list_dns_records",
    "list_domains",
    "list_edge_configs",
    "list_project_domains",
    "list_projects",
    "list_team_members",
    "list_teams",
    "list_webhooks",
    "pause_project",
    "promote_deployment",
    "remove_project_domain",
    "rerequest_check",
    "unpause_project",
    "update_check",
    "update_dns_record",
    "update_edge_config_items",
    "update_env_var",
    "update_project",
    "update_project_domain",
    "verify_project_domain",
]

_BASE_URL = "https://api.vercel.com"
_TIMEOUT = 30.0
_EMPTY_KEY_ERROR = "Vercel API key is empty. Please configure a valid Vercel credential."


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _team_params(team_id: str | None) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if team_id:
        params["teamId"] = team_id.strip()
    return params


# --- Input schemas (args_schema for each @tool) ----------------------------


class ListDeploymentsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str | None = Field(
        default=None, description="Filter deployments by project ID or name"
    )
    target: str | None = Field(
        default=None, description="Filter by environment: production or staging"
    )
    state: str | None = Field(
        default=None,
        description=(
            "Filter by state: BUILDING, ERROR, INITIALIZING, QUEUED, READY, CANCELED, BLOCKED"
        ),
    )
    app: str | None = Field(default=None, description="Filter by deployment name")
    since: int | None = Field(
        default=None, description="Get deployments created after this timestamp"
    )
    until: int | None = Field(
        default=None, description="Get deployments created before this timestamp"
    )
    limit: int | None = Field(default=None, description="Maximum number of deployments to return")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetDeploymentInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="The unique deployment identifier or hostname")
    with_git_repo_info: str | None = Field(
        default=None, description="Whether to add gitRepo information (true/false)"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateDeploymentInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    name: str = Field(description="Project name for the deployment")
    project: str | None = Field(
        default=None, description="Project ID (overrides name for project lookup)"
    )
    deployment_id: str | None = Field(
        default=None, description="Existing deployment ID to redeploy"
    )
    target: str | None = Field(
        default=None, description="Target environment: production, staging, or a custom environment"
    )
    git_source: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Git Repository source to deploy "
            '(e.g. {"type":"github","repo":"owner/repo","ref":"main"})'
        ),
    )
    force_new: str | None = Field(
        default=None, description="Force a new deployment even if a similar one exists (0 or 1)"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CancelDeploymentInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="The deployment ID to cancel")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteDeploymentInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="The deployment ID or URL to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetDeploymentEventsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="The unique deployment identifier or hostname")
    direction: str | None = Field(
        default=None, description="Order of events by timestamp: backward or forward"
    )
    follow: int | None = Field(
        default=None, description="When set to 1, returns live events as they happen"
    )
    limit: int | None = Field(
        default=None, description="Maximum number of events to return (-1 for all)"
    )
    since: int | None = Field(
        default=None, description="Timestamp to start pulling build logs from"
    )
    until: int | None = Field(default=None, description="Timestamp to stop pulling build logs at")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListDeploymentFilesInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="The deployment ID to list files for")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class PromoteDeploymentInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    deployment_id: str = Field(description="The ID of the deployment to promote to production")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListProjectsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    search: str | None = Field(default=None, description="Search projects by name")
    limit: int | None = Field(default=None, description="Maximum number of projects to return")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetProjectInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateProjectInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    name: str = Field(description="Project name")
    framework: str | None = Field(
        default=None, description="Project framework (e.g. nextjs, remix, vite)"
    )
    git_repository: dict[str, Any] | None = Field(
        default=None, description="Git repository connection object with type and repo"
    )
    build_command: str | None = Field(default=None, description="Custom build command")
    output_directory: str | None = Field(default=None, description="Custom output directory")
    install_command: str | None = Field(default=None, description="Custom install command")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UpdateProjectInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    name: str | None = Field(default=None, description="New project name")
    framework: str | None = Field(
        default=None, description="Project framework (e.g. nextjs, remix, vite)"
    )
    build_command: str | None = Field(default=None, description="Custom build command")
    output_directory: str | None = Field(default=None, description="Custom output directory")
    install_command: str | None = Field(default=None, description="Custom install command")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteProjectInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class PauseProjectInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UnpauseProjectInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListProjectDomainsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")
    limit: int | None = Field(default=None, description="Maximum number of domains to return")


class AddProjectDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    domain: str = Field(description="Domain name to add")
    redirect: str | None = Field(default=None, description="Target domain for redirect")
    redirect_status_code: int | None = Field(
        default=None, description="HTTP status code for redirect (301, 302, 307, 308)"
    )
    git_branch: str | None = Field(default=None, description="Git branch to link the domain to")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UpdateProjectDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    domain: str = Field(description="Domain name to update")
    redirect: str | None = Field(default=None, description="Target destination domain for redirect")
    redirect_status_code: int | None = Field(
        default=None, description="HTTP status code for redirect (301, 302, 307, 308)"
    )
    git_branch: str | None = Field(default=None, description="Git branch to link the domain to")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class VerifyProjectDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    domain: str = Field(description="Domain name to verify")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class RemoveProjectDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    domain: str = Field(description="Domain name to remove")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetEnvVarsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateEnvVarInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    key: str = Field(description="Environment variable name")
    value: str = Field(description="Environment variable value")
    target: str = Field(
        description="Comma-separated target environments (production, preview, development)"
    )
    type: str | None = Field(
        default=None,
        description=(
            "Variable type: system, encrypted, plain, or sensitive (default: plain)"
        )
    )
    git_branch: str | None = Field(
        default=None, description="Git branch to associate (requires target to include preview)"
    )
    comment: str | None = Field(
        default=None, description="Comment to add context (max 500 characters)"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UpdateEnvVarInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    env_id: str = Field(description="Environment variable ID to update")
    key: str | None = Field(default=None, description="New variable name")
    value: str | None = Field(default=None, description="New variable value")
    target: str | None = Field(
        default=None,
        description="Comma-separated target environments (production, preview, development)",
    )
    type: str | None = Field(
        default=None, description="Variable type: system, encrypted, plain, or sensitive"
    )
    git_branch: str | None = Field(
        default=None, description="Git branch to associate (requires target to include preview)"
    )
    comment: str | None = Field(
        default=None, description="Comment to add context (max 500 characters)"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteEnvVarInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str = Field(description="Project ID or name")
    env_id: str = Field(description="Environment variable ID to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListDomainsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Maximum number of domains to return")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    domain: str = Field(description="The domain name to retrieve")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class AddDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    name: str = Field(description="The domain name to add")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteDomainInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    domain: str = Field(description="The domain name to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetDomainConfigInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    domain: str = Field(description="The domain name to get configuration for")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListDnsRecordsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    domain: str = Field(description="The domain name to list records for")
    limit: int | None = Field(default=None, description="Maximum number of records to return")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateDnsRecordInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    domain: str = Field(description="The domain name to create the record for")
    record_name: str = Field(description="The subdomain or record name")
    record_type: str = Field(
        description="DNS record type (A, AAAA, ALIAS, CAA, CNAME, HTTPS, MX, SRV, TXT, NS)"
    )
    value: str = Field(description="The value of the DNS record")
    ttl: int | None = Field(default=None, description="Time to live in seconds")
    mx_priority: int | None = Field(default=None, description="Priority for MX records")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UpdateDnsRecordInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    record_id: str = Field(description="The ID of the DNS record to update")
    name: str | None = Field(default=None, description="The name of the DNS record")
    value: str | None = Field(default=None, description="The value of the DNS record")
    type: str | None = Field(
        default=None,
        description="DNS record type (A, AAAA, ALIAS, CAA, CNAME, HTTPS, MX, SRV, TXT, NS)",
    )
    ttl: int | None = Field(default=None, description="Time to live in seconds (60 to 2147483647)")
    mx_priority: int | None = Field(default=None, description="Priority for MX records")
    comment: str | None = Field(
        default=None, description="Comment to add context (max 500 characters)"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteDnsRecordInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    domain: str = Field(description="The domain name the record belongs to")
    record_id: str = Field(description="The ID of the DNS record to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListAliasesInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str | None = Field(default=None, description="Filter aliases by project ID")
    domain: str | None = Field(default=None, description="Filter aliases by domain")
    limit: int | None = Field(default=None, description="Maximum number of aliases to return")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetAliasInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    alias_id: str = Field(description="Alias ID or hostname to look up")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateAliasInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="Deployment ID to assign the alias to")
    alias: str = Field(description="The domain or subdomain to assign as an alias")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteAliasInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    alias_id: str = Field(description="Alias ID to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListEdgeConfigsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetEdgeConfigInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    edge_config_id: str = Field(description="Edge Config ID to look up")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateEdgeConfigInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    slug: str = Field(description="The name/slug for the new Edge Config")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class DeleteEdgeConfigInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    edge_config_id: str = Field(description="Edge Config ID to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetEdgeConfigItemsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    edge_config_id: str = Field(description="Edge Config ID to get items from")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UpdateEdgeConfigItemsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    edge_config_id: str = Field(description="Edge Config ID to update items in")
    items: list[dict[str, Any]] = Field(
        description=(
            "Array of operations: "
            '[{"operation": "create|update|upsert|delete", "key": "...", "value": ...}]'
        )
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListTeamsInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    limit: int | None = Field(default=None, description="Maximum number of teams to return")
    since: int | None = Field(
        default=None, description="Only include teams created since this timestamp (ms)"
    )
    until: int | None = Field(
        default=None, description="Only include teams created until this timestamp (ms)"
    )


class GetTeamInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    team_id: str = Field(description="The team ID to retrieve")


class ListTeamMembersInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    team_id: str = Field(description="The team ID to list members for")
    limit: int | None = Field(default=None, description="Maximum number of members to return")
    role: str | None = Field(
        default=None,
        description=(
            "Filter by role (OWNER, MEMBER, DEVELOPER, SECURITY, BILLING, VIEWER, CONTRIBUTOR)"
        ),
    )
    since: int | None = Field(
        default=None, description="Only include members added since this timestamp (ms)"
    )
    until: int | None = Field(
        default=None, description="Only include members added until this timestamp (ms)"
    )
    search: str | None = Field(
        default=None, description="Search members by name, username, and email"
    )


class GetUserInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")


class ListWebhooksInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    project_id: str | None = Field(default=None, description="Filter webhooks by project ID")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetWebhookInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    webhook_id: str = Field(description="Webhook ID to look up")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateWebhookInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    url: str = Field(description="Webhook URL (must be https)")
    events: str = Field(description="Comma-separated event names to subscribe to")
    project_ids: str | None = Field(
        default=None, description="Comma-separated project IDs to scope the webhook to"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the webhook to")


class DeleteWebhookInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    webhook_id: str = Field(description="The webhook ID to delete")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class CreateCheckInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="Deployment ID to create the check for")
    name: str = Field(description="Name of the check (max 100 characters)")
    blocking: bool = Field(description="Whether the check blocks the deployment")
    path: str | None = Field(default=None, description="Page path being checked")
    details_url: str | None = Field(default=None, description="URL with details about the check")
    external_id: str | None = Field(default=None, description="External identifier for the check")
    rerequestable: bool | None = Field(
        default=None, description="Whether the check can be rerequested"
    )
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class GetCheckInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="Deployment ID the check belongs to")
    check_id: str = Field(description="Check ID to retrieve")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class ListChecksInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="Deployment ID to list checks for")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class UpdateCheckInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="Deployment ID the check belongs to")
    check_id: str = Field(description="Check ID to update")
    name: str | None = Field(default=None, description="Updated name of the check")
    status: str | None = Field(default=None, description="Updated status: running or completed")
    conclusion: str | None = Field(
        default=None,
        description=(
            "Check conclusion: canceled, failed, neutral, succeeded, or skipped"
        )
    )
    details_url: str | None = Field(default=None, description="URL with details about the check")
    external_id: str | None = Field(default=None, description="External identifier for the check")
    path: str | None = Field(default=None, description="Page path being checked")
    output: dict[str, Any] | None = Field(default=None, description="Check output metrics object")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


class RerequestCheckInput(BaseModel):
    api_key: str = Field(description="Vercel API key (provided by credential system)")
    deployment_id: str = Field(description="Deployment ID the check belongs to")
    check_id: str = Field(description="Check ID to rerequest")
    team_id: str | None = Field(default=None, description="Team ID to scope the request")


# --- Deployments -----------------------------------------------------------


@tool(args_schema=ListDeploymentsInput)
@serialize_pydantic_return
async def list_deployments(
    api_key: str,
    project_id: str | None = None,
    target: str | None = None,
    state: str | None = None,
    app: str | None = None,
    since: int | None = None,
    until: int | None = None,
    limit: int | None = None,
    team_id: str | None = None,
) -> ListDeploymentsOutput:
    """List deployments for a Vercel project or team."""
    if not api_key or not api_key.strip():
        return ListDeploymentsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if project_id:
        params["projectId"] = project_id.strip()
    if target:
        params["target"] = target
    if state:
        params["state"] = state
    if app:
        params["app"] = app.strip()
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    if limit is not None:
        params["limit"] = limit
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v7/deployments", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListDeploymentsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDeploymentsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDeploymentsOutput(success=False, error=f"List deployments failed: {exc}")

    deployments = data.get("deployments") or []
    return ListDeploymentsOutput(
        success=True,
        deployments=[
            DeploymentItem.model_validate(
                {
                    "uid": d.get("uid"),
                    "name": d.get("name"),
                    "url": d.get("url"),
                    "state": d.get("state") or d.get("readyState"),
                    "target": d.get("target"),
                    "created": d.get("created") or d.get("createdAt"),
                    "project_id": d.get("projectId"),
                    "source": d.get("source"),
                    "inspector_url": d.get("inspectorUrl"),
                    "checks_state": d.get("checksState"),
                    "checks_conclusion": d.get("checksConclusion"),
                    "error_message": d.get("errorMessage"),
                    "creator": d.get("creator"),
                    "meta": d.get("meta") or {},
                }
            )
            for d in deployments
        ],
        count=len(deployments),
        has_more=(data.get("pagination") or {}).get("next") is not None,
    )


@tool(args_schema=GetDeploymentInput)
@serialize_pydantic_return
async def get_deployment(
    api_key: str,
    deployment_id: str,
    with_git_repo_info: str | None = None,
    team_id: str | None = None,
) -> GetDeploymentOutput:
    """Get details of a specific Vercel deployment."""
    if not api_key or not api_key.strip():
        return GetDeploymentOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if with_git_repo_info:
        params["withGitRepoInfo"] = with_git_repo_info
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v13/deployments/{deployment_id.strip()}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetDeploymentOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDeploymentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDeploymentOutput(success=False, error=f"Get deployment failed: {exc}")

    return GetDeploymentOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        url=data.get("url"),
        ready_state=data.get("readyState"),
        status=data.get("status") or data.get("readyState"),
        target=data.get("target"),
        created_at=data.get("createdAt") or data.get("created"),
        building_at=data.get("buildingAt"),
        ready=data.get("ready"),
        source=data.get("source"),
        alias=data.get("alias") or [],
        regions=data.get("regions") or [],
        inspector_url=data.get("inspectorUrl"),
        project_id=data.get("projectId"),
        creator=data.get("creator"),
        project=data.get("project"),
        meta=data.get("meta") or {},
        git_source=data.get("gitSource"),
        error_code=data.get("errorCode"),
        error_message=data.get("errorMessage"),
        alias_assigned=data.get("aliasAssigned"),
    )


@tool(args_schema=CreateDeploymentInput)
@serialize_pydantic_return
async def create_deployment(
    api_key: str,
    name: str,
    project: str | None = None,
    deployment_id: str | None = None,
    target: str | None = None,
    git_source: dict[str, Any] | None = None,
    force_new: str | None = None,
    team_id: str | None = None,
) -> CreateDeploymentOutput:
    """Create a new deployment or redeploy an existing one."""
    if not api_key or not api_key.strip():
        return CreateDeploymentOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if force_new:
        params["forceNew"] = force_new
    params.update(_team_params(team_id))

    body: dict[str, Any] = {"name": name.strip()}
    if project:
        body["project"] = project.strip()
    if deployment_id:
        body["deploymentId"] = deployment_id.strip()
    if target:
        body["target"] = target
    if git_source:
        body["gitSource"] = git_source

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v13/deployments",
                headers=_headers(api_key),
                params=params,
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateDeploymentOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDeploymentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDeploymentOutput(success=False, error=f"Create deployment failed: {exc}")

    return CreateDeploymentOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        url=data.get("url"),
        ready_state=data.get("readyState"),
        project_id=data.get("projectId"),
        created_at=data.get("createdAt") or data.get("created"),
        alias=data.get("alias") or [],
        target=data.get("target"),
        inspector_url=data.get("inspectorUrl"),
        error_code=data.get("errorCode"),
        error_message=data.get("errorMessage"),
        alias_assigned=data.get("aliasAssigned"),
    )


@tool(args_schema=CancelDeploymentInput)
@serialize_pydantic_return
async def cancel_deployment(
    api_key: str,
    deployment_id: str,
    team_id: str | None = None,
) -> CancelDeploymentOutput:
    """Cancel a running Vercel deployment."""
    if not api_key or not api_key.strip():
        return CancelDeploymentOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v12/deployments/{deployment_id.strip()}/cancel",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return CancelDeploymentOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CancelDeploymentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CancelDeploymentOutput(success=False, error=f"Cancel deployment failed: {exc}")

    return CancelDeploymentOutput(
        success=True,
        id=data.get("id") or data.get("uid"),
        name=data.get("name"),
        state=data.get("readyState") or data.get("state") or "CANCELED",
        url=data.get("url"),
        status=data.get("status"),
        project_id=data.get("projectId"),
        inspector_url=data.get("inspectorUrl"),
    )


@tool(args_schema=DeleteDeploymentInput)
@serialize_pydantic_return
async def delete_deployment(
    api_key: str,
    deployment_id: str,
    team_id: str | None = None,
) -> DeleteDeploymentOutput:
    """Delete a Vercel deployment."""
    if not api_key or not api_key.strip():
        return DeleteDeploymentOutput(success=False, error=_EMPTY_KEY_ERROR)

    deployment = deployment_id.strip()
    params: dict[str, Any] = _team_params(team_id)
    if "." in deployment:
        params["url"] = deployment

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v13/deployments/{deployment}",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return DeleteDeploymentOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteDeploymentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteDeploymentOutput(success=False, error=f"Delete deployment failed: {exc}")

    return DeleteDeploymentOutput(
        success=True,
        uid=data.get("uid") or data.get("id"),
        state=data.get("state") or "DELETED",
    )


@tool(args_schema=GetDeploymentEventsInput)
@serialize_pydantic_return
async def get_deployment_events(
    api_key: str,
    deployment_id: str,
    direction: str | None = None,
    follow: int | None = None,
    limit: int | None = None,
    since: int | None = None,
    until: int | None = None,
    team_id: str | None = None,
) -> GetDeploymentEventsOutput:
    """Get build and runtime events for a Vercel deployment."""
    if not api_key or not api_key.strip():
        return GetDeploymentEventsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if direction:
        params["direction"] = direction
    if follow is not None:
        params["follow"] = follow
    if limit is not None:
        params["limit"] = limit
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v3/deployments/{deployment_id.strip()}/events",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return GetDeploymentEventsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDeploymentEventsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDeploymentEventsOutput(
            success=False, error=f"Get deployment events failed: {exc}"
        )

    raw = data if isinstance(data, list) else (data.get("events") or [])
    events = [
        DeploymentEvent.model_validate(
            {
                "type": e.get("type"),
                "created": e.get("created"),
                "date": e.get("date") or (e.get("payload") or {}).get("date"),
                "text": e.get("text") or (e.get("payload") or {}).get("text"),
                "serial": e.get("serial") or (e.get("payload") or {}).get("serial"),
                "deployment_id": (
                    e.get("deploymentId") or (e.get("payload") or {}).get("deploymentId")
                ),
                "id": e.get("id") or (e.get("payload") or {}).get("id"),
                "level": e.get("level"),
                "info": e.get("info") or (e.get("payload") or {}).get("info"),
            }
        )
        for e in raw
    ]
    return GetDeploymentEventsOutput(success=True, events=events, count=len(events))


@tool(args_schema=ListDeploymentFilesInput)
@serialize_pydantic_return
async def list_deployment_files(
    api_key: str,
    deployment_id: str,
    team_id: str | None = None,
) -> ListDeploymentFilesOutput:
    """List file-tree metadata for a Vercel deployment."""
    if not api_key or not api_key.strip():
        return ListDeploymentFilesOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v6/deployments/{deployment_id.strip()}/files",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return ListDeploymentFilesOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDeploymentFilesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDeploymentFilesOutput(
            success=False, error=f"List deployment files failed: {exc}"
        )

    raw = data if isinstance(data, list) else (data.get("files") or [])
    files = [
        DeploymentFile.model_validate(
            {
                "name": f.get("name"),
                "type": f.get("type"),
                "uid": f.get("uid"),
                "mode": f.get("mode"),
                "content_type": f.get("contentType"),
                "children": f.get("children") or [],
            }
        )
        for f in raw
    ]
    return ListDeploymentFilesOutput(success=True, files=files, count=len(files))


@tool(args_schema=PromoteDeploymentInput)
@serialize_pydantic_return
async def promote_deployment(
    api_key: str,
    project_id: str,
    deployment_id: str,
    team_id: str | None = None,
) -> PromoteDeploymentOutput:
    """Promote a deployment to production for the given project."""
    if not api_key or not api_key.strip():
        return PromoteDeploymentOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v10/projects/{project_id.strip()}/promote/{deployment_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 201):
            return PromoteDeploymentOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return PromoteDeploymentOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PromoteDeploymentOutput(success=False, error=f"Promote deployment failed: {exc}")

    return PromoteDeploymentOutput(success=True, promoted=True)


# --- Projects --------------------------------------------------------------


@tool(args_schema=ListProjectsInput)
@serialize_pydantic_return
async def list_projects(
    api_key: str,
    search: str | None = None,
    limit: int | None = None,
    team_id: str | None = None,
) -> ListProjectsOutput:
    """List all projects in a Vercel team or account."""
    if not api_key or not api_key.strip():
        return ListProjectsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if search:
        params["search"] = search
    if limit is not None:
        params["limit"] = limit
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v10/projects", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListProjectsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListProjectsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProjectsOutput(success=False, error=f"List projects failed: {exc}")

    projects = data.get("projects") or []
    return ListProjectsOutput(
        success=True,
        projects=[
            ProjectItem.model_validate(
                {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "framework": p.get("framework"),
                    "created_at": p.get("createdAt"),
                    "updated_at": p.get("updatedAt"),
                }
            )
            for p in projects
        ],
        count=len(projects),
        has_more=(data.get("pagination") or {}).get("next") is not None,
    )


@tool(args_schema=GetProjectInput)
@serialize_pydantic_return
async def get_project(
    api_key: str,
    project_id: str,
    team_id: str | None = None,
) -> GetProjectOutput:
    """Get details of a specific Vercel project."""
    if not api_key or not api_key.strip():
        return GetProjectOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetProjectOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetProjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetProjectOutput(success=False, error=f"Get project failed: {exc}")

    return GetProjectOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        framework=data.get("framework"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        link=data.get("link"),
    )


@tool(args_schema=CreateProjectInput)
@serialize_pydantic_return
async def create_project(
    api_key: str,
    name: str,
    framework: str | None = None,
    git_repository: dict[str, Any] | None = None,
    build_command: str | None = None,
    output_directory: str | None = None,
    install_command: str | None = None,
    team_id: str | None = None,
) -> CreateProjectOutput:
    """Create a new Vercel project."""
    if not api_key or not api_key.strip():
        return CreateProjectOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": name.strip()}
    if framework:
        body["framework"] = framework.strip()
    if git_repository:
        body["gitRepository"] = git_repository
    if build_command:
        body["buildCommand"] = build_command.strip()
    if output_directory:
        body["outputDirectory"] = output_directory.strip()
    if install_command:
        body["installCommand"] = install_command.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v11/projects",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateProjectOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateProjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateProjectOutput(success=False, error=f"Create project failed: {exc}")

    return CreateProjectOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        framework=data.get("framework"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=UpdateProjectInput)
@serialize_pydantic_return
async def update_project(
    api_key: str,
    project_id: str,
    name: str | None = None,
    framework: str | None = None,
    build_command: str | None = None,
    output_directory: str | None = None,
    install_command: str | None = None,
    team_id: str | None = None,
) -> UpdateProjectOutput:
    """Update an existing Vercel project."""
    if not api_key or not api_key.strip():
        return UpdateProjectOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if name:
        body["name"] = name.strip()
    if framework:
        body["framework"] = framework.strip()
    if build_command:
        body["buildCommand"] = build_command.strip()
    if output_directory:
        body["outputDirectory"] = output_directory.strip()
    if install_command:
        body["installCommand"] = install_command.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code != 200:
            return UpdateProjectOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateProjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateProjectOutput(success=False, error=f"Update project failed: {exc}")

    return UpdateProjectOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        framework=data.get("framework"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=DeleteProjectInput)
@serialize_pydantic_return
async def delete_project(
    api_key: str,
    project_id: str,
    team_id: str | None = None,
) -> DeleteProjectOutput:
    """Delete a Vercel project."""
    if not api_key or not api_key.strip():
        return DeleteProjectOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return DeleteProjectOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return DeleteProjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteProjectOutput(success=False, error=f"Delete project failed: {exc}")

    return DeleteProjectOutput(success=True, deleted=True)


@tool(args_schema=PauseProjectInput)
@serialize_pydantic_return
async def pause_project(
    api_key: str,
    project_id: str,
    team_id: str | None = None,
) -> PauseProjectOutput:
    """Pause a Vercel project."""
    if not api_key or not api_key.strip():
        return PauseProjectOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/projects/{project_id.strip()}/pause",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 201, 204):
            return PauseProjectOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        try:
            data = response.json()
        except Exception:
            data = {}
    except httpx.TimeoutException:
        return PauseProjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return PauseProjectOutput(success=False, error=f"Pause project failed: {exc}")

    return PauseProjectOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        paused=data.get("paused", True),
    )


@tool(args_schema=UnpauseProjectInput)
@serialize_pydantic_return
async def unpause_project(
    api_key: str,
    project_id: str,
    team_id: str | None = None,
) -> UnpauseProjectOutput:
    """Unpause a Vercel project."""
    if not api_key or not api_key.strip():
        return UnpauseProjectOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/projects/{project_id.strip()}/unpause",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 201, 204):
            return UnpauseProjectOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        try:
            data = response.json()
        except Exception:
            data = {}
    except httpx.TimeoutException:
        return UnpauseProjectOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UnpauseProjectOutput(success=False, error=f"Unpause project failed: {exc}")

    return UnpauseProjectOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        paused=data.get("paused", False),
    )


# --- Project domains -------------------------------------------------------


@tool(args_schema=ListProjectDomainsInput)
@serialize_pydantic_return
async def list_project_domains(
    api_key: str,
    project_id: str,
    team_id: str | None = None,
    limit: int | None = None,
) -> ListProjectDomainsOutput:
    """List all domains for a Vercel project."""
    if not api_key or not api_key.strip():
        return ListProjectDomainsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = _team_params(team_id)
    if limit is not None:
        params["limit"] = limit

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}/domains",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListProjectDomainsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListProjectDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListProjectDomainsOutput(success=False, error=f"List project domains failed: {exc}")

    domains = data.get("domains") or []
    return ListProjectDomainsOutput(
        success=True,
        domains=[
            ProjectDomainItem.model_validate(
                {
                    "name": d.get("name"),
                    "apex_name": d.get("apexName"),
                    "project_id": d.get("projectId"),
                    "redirect": d.get("redirect"),
                    "redirect_status_code": d.get("redirectStatusCode"),
                    "verified": d.get("verified"),
                    "git_branch": d.get("gitBranch"),
                    "verification": d.get("verification") or [],
                    "created_at": d.get("createdAt"),
                    "updated_at": d.get("updatedAt"),
                }
            )
            for d in domains
        ],
        count=len(domains),
        has_more=(data.get("pagination") or {}).get("next") is not None,
    )


@tool(args_schema=AddProjectDomainInput)
@serialize_pydantic_return
async def add_project_domain(
    api_key: str,
    project_id: str,
    domain: str,
    redirect: str | None = None,
    redirect_status_code: int | None = None,
    git_branch: str | None = None,
    team_id: str | None = None,
) -> AddProjectDomainOutput:
    """Add a domain to a Vercel project."""
    if not api_key or not api_key.strip():
        return AddProjectDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": domain.strip()}
    if redirect:
        body["redirect"] = redirect.strip()
    if redirect_status_code:
        body["redirectStatusCode"] = redirect_status_code
    if git_branch:
        body["gitBranch"] = git_branch.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v10/projects/{project_id.strip()}/domains",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return AddProjectDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddProjectDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddProjectDomainOutput(success=False, error=f"Add project domain failed: {exc}")

    return AddProjectDomainOutput(
        success=True,
        name=data.get("name"),
        apex_name=data.get("apexName"),
        project_id=data.get("projectId"),
        verified=data.get("verified"),
        git_branch=data.get("gitBranch"),
        redirect=data.get("redirect"),
        redirect_status_code=data.get("redirectStatusCode"),
        verification=data.get("verification") or [],
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=UpdateProjectDomainInput)
@serialize_pydantic_return
async def update_project_domain(
    api_key: str,
    project_id: str,
    domain: str,
    redirect: str | None = None,
    redirect_status_code: int | None = None,
    git_branch: str | None = None,
    team_id: str | None = None,
) -> UpdateProjectDomainOutput:
    """Update a project domain's configuration on Vercel."""
    if not api_key or not api_key.strip():
        return UpdateProjectDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if redirect:
        body["redirect"] = redirect.strip()
    if redirect_status_code:
        body["redirectStatusCode"] = redirect_status_code
    if git_branch:
        body["gitBranch"] = git_branch.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}/domains/{domain.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code != 200:
            return UpdateProjectDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateProjectDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateProjectDomainOutput(
            success=False, error=f"Update project domain failed: {exc}"
        )

    return UpdateProjectDomainOutput(
        success=True,
        name=data.get("name"),
        apex_name=data.get("apexName"),
        project_id=data.get("projectId"),
        verified=data.get("verified"),
        redirect=data.get("redirect"),
        redirect_status_code=data.get("redirectStatusCode"),
        git_branch=data.get("gitBranch"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        verification=data.get("verification") or [],
    )


@tool(args_schema=VerifyProjectDomainInput)
@serialize_pydantic_return
async def verify_project_domain(
    api_key: str,
    project_id: str,
    domain: str,
    team_id: str | None = None,
) -> VerifyProjectDomainOutput:
    """Verify a Vercel project domain by checking its verification challenge."""
    if not api_key or not api_key.strip():
        return VerifyProjectDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}/domains/{domain.strip()}/verify",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return VerifyProjectDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        try:
            data = response.json()
        except Exception:
            data = {}
    except httpx.TimeoutException:
        return VerifyProjectDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return VerifyProjectDomainOutput(
            success=False, error=f"Verify project domain failed: {exc}"
        )

    return VerifyProjectDomainOutput(
        success=True,
        name=data.get("name"),
        apex_name=data.get("apexName"),
        project_id=data.get("projectId"),
        verified=data.get("verified", False),
        redirect=data.get("redirect"),
        redirect_status_code=data.get("redirectStatusCode"),
        git_branch=data.get("gitBranch"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=RemoveProjectDomainInput)
@serialize_pydantic_return
async def remove_project_domain(
    api_key: str,
    project_id: str,
    domain: str,
    team_id: str | None = None,
) -> RemoveProjectDomainOutput:
    """Remove a domain from a Vercel project."""
    if not api_key or not api_key.strip():
        return RemoveProjectDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}/domains/{domain.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return RemoveProjectDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return RemoveProjectDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RemoveProjectDomainOutput(
            success=False, error=f"Remove project domain failed: {exc}"
        )

    return RemoveProjectDomainOutput(success=True, deleted=True)


# --- Environment variables -------------------------------------------------


@tool(args_schema=GetEnvVarsInput)
@serialize_pydantic_return
async def get_env_vars(
    api_key: str,
    project_id: str,
    team_id: str | None = None,
) -> GetEnvVarsOutput:
    """Retrieve environment variables for a Vercel project."""
    if not api_key or not api_key.strip():
        return GetEnvVarsOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v10/projects/{project_id.strip()}/env",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetEnvVarsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEnvVarsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEnvVarsOutput(success=False, error=f"Get environment variables failed: {exc}")

    envs = data.get("envs") or []
    return GetEnvVarsOutput(
        success=True,
        envs=[
            EnvVarItem.model_validate(
                {
                    "id": e.get("id"),
                    "key": e.get("key"),
                    "value": e.get("value"),
                    "type": e.get("type"),
                    "target": e.get("target") or [],
                    "git_branch": e.get("gitBranch"),
                    "comment": e.get("comment"),
                    "created_at": e.get("createdAt"),
                    "updated_at": e.get("updatedAt"),
                }
            )
            for e in envs
        ],
        count=len(envs),
    )


@tool(args_schema=CreateEnvVarInput)
@serialize_pydantic_return
async def create_env_var(
    api_key: str,
    project_id: str,
    key: str,
    value: str,
    target: str,
    type: str | None = None,
    git_branch: str | None = None,
    comment: str | None = None,
    team_id: str | None = None,
) -> CreateEnvVarOutput:
    """Create an environment variable for a Vercel project."""
    if not api_key or not api_key.strip():
        return CreateEnvVarOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "key": key,
        "value": value,
        "target": [t.strip() for t in target.split(",")],
        "type": type or "plain",
    }
    if git_branch:
        body["gitBranch"] = git_branch
    if comment:
        body["comment"] = comment

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v10/projects/{project_id.strip()}/env",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateEnvVarOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateEnvVarOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEnvVarOutput(success=False, error=f"Create environment variable failed: {exc}")

    env = data.get("created") or data
    return CreateEnvVarOutput(
        success=True,
        id=env.get("id"),
        key=env.get("key"),
        value=env.get("value"),
        type=env.get("type"),
        target=env.get("target") or [],
        git_branch=env.get("gitBranch"),
        comment=env.get("comment"),
        created_at=env.get("createdAt"),
        updated_at=env.get("updatedAt"),
    )


@tool(args_schema=UpdateEnvVarInput)
@serialize_pydantic_return
async def update_env_var(
    api_key: str,
    project_id: str,
    env_id: str,
    key: str | None = None,
    value: str | None = None,
    target: str | None = None,
    type: str | None = None,
    git_branch: str | None = None,
    comment: str | None = None,
    team_id: str | None = None,
) -> UpdateEnvVarOutput:
    """Update an environment variable for a Vercel project."""
    if not api_key or not api_key.strip():
        return UpdateEnvVarOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if key:
        body["key"] = key
    if value:
        body["value"] = value
    if target:
        body["target"] = [t.strip() for t in target.split(",")]
    if type:
        body["type"] = type
    if git_branch:
        body["gitBranch"] = git_branch
    if comment:
        body["comment"] = comment

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}/env/{env_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code != 200:
            return UpdateEnvVarOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateEnvVarOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateEnvVarOutput(success=False, error=f"Update environment variable failed: {exc}")

    return UpdateEnvVarOutput(
        success=True,
        id=data.get("id"),
        key=data.get("key"),
        value=data.get("value"),
        type=data.get("type"),
        target=data.get("target") or [],
        git_branch=data.get("gitBranch"),
        comment=data.get("comment"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=DeleteEnvVarInput)
@serialize_pydantic_return
async def delete_env_var(
    api_key: str,
    project_id: str,
    env_id: str,
    team_id: str | None = None,
) -> DeleteEnvVarOutput:
    """Delete an environment variable from a Vercel project."""
    if not api_key or not api_key.strip():
        return DeleteEnvVarOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v9/projects/{project_id.strip()}/env/{env_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return DeleteEnvVarOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return DeleteEnvVarOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteEnvVarOutput(success=False, error=f"Delete environment variable failed: {exc}")

    return DeleteEnvVarOutput(success=True, deleted=True)


# --- Account domains -------------------------------------------------------


@tool(args_schema=ListDomainsInput)
@serialize_pydantic_return
async def list_domains(
    api_key: str,
    limit: int | None = None,
    team_id: str | None = None,
) -> ListDomainsOutput:
    """List all domains in a Vercel account or team."""
    if not api_key or not api_key.strip():
        return ListDomainsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v5/domains", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListDomainsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDomainsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDomainsOutput(success=False, error=f"List domains failed: {exc}")

    domains = data.get("domains") or []
    return ListDomainsOutput(
        success=True,
        domains=[
            DomainItem.model_validate(
                {
                    "id": d.get("id"),
                    "name": d.get("name"),
                    "verified": d.get("verified", False),
                    "created_at": d.get("createdAt"),
                    "expires_at": d.get("expiresAt"),
                    "service_type": d.get("serviceType"),
                    "nameservers": d.get("nameservers") or [],
                    "intended_nameservers": d.get("intendedNameservers") or [],
                    "renew": d.get("renew", False),
                    "bought_at": d.get("boughtAt"),
                    "transferred_at": d.get("transferredAt"),
                    "creator": d.get("creator"),
                }
            )
            for d in domains
        ],
        count=len(domains),
        has_more=(data.get("pagination") or {}).get("next") is not None,
    )


@tool(args_schema=GetDomainInput)
@serialize_pydantic_return
async def get_domain(
    api_key: str,
    domain: str,
    team_id: str | None = None,
) -> GetDomainOutput:
    """Get information about a specific domain in a Vercel account."""
    if not api_key or not api_key.strip():
        return GetDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v5/domains/{domain.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDomainOutput(success=False, error=f"Get domain failed: {exc}")

    d = data.get("domain") or data
    return GetDomainOutput(
        success=True,
        id=d.get("id"),
        name=d.get("name"),
        verified=d.get("verified", False),
        created_at=d.get("createdAt"),
        expires_at=d.get("expiresAt"),
        service_type=d.get("serviceType"),
        nameservers=d.get("nameservers") or [],
        intended_nameservers=d.get("intendedNameservers") or [],
        custom_nameservers=d.get("customNameservers") or [],
        renew=d.get("renew", False),
        bought_at=d.get("boughtAt"),
        transferred_at=d.get("transferredAt"),
        creator=d.get("creator"),
        user_id=d.get("userId"),
        team_id=d.get("teamId"),
        transfer_started_at=d.get("transferStartedAt"),
    )


@tool(args_schema=AddDomainInput)
@serialize_pydantic_return
async def add_domain(
    api_key: str,
    name: str,
    team_id: str | None = None,
) -> AddDomainOutput:
    """Add a new domain to a Vercel account or team."""
    if not api_key or not api_key.strip():
        return AddDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"method": "add", "name": name.strip()}

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v7/domains",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return AddDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return AddDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return AddDomainOutput(success=False, error=f"Add domain failed: {exc}")

    d = data.get("domain") or data
    return AddDomainOutput(
        success=True,
        id=d.get("id"),
        name=d.get("name"),
        verified=d.get("verified", False),
        created_at=d.get("createdAt"),
        service_type=d.get("serviceType"),
        nameservers=d.get("nameservers") or [],
        intended_nameservers=d.get("intendedNameservers") or [],
        expires_at=d.get("expiresAt"),
        custom_nameservers=d.get("customNameservers") or [],
        renew=d.get("renew"),
        bought_at=d.get("boughtAt"),
        transferred_at=d.get("transferredAt"),
        creator=d.get("creator"),
    )


@tool(args_schema=DeleteDomainInput)
@serialize_pydantic_return
async def delete_domain(
    api_key: str,
    domain: str,
    team_id: str | None = None,
) -> DeleteDomainOutput:
    """Delete a domain from a Vercel account or team."""
    if not api_key or not api_key.strip():
        return DeleteDomainOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v6/domains/{domain.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return DeleteDomainOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        try:
            data = response.json()
        except Exception:
            data = {}
    except httpx.TimeoutException:
        return DeleteDomainOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteDomainOutput(success=False, error=f"Delete domain failed: {exc}")

    return DeleteDomainOutput(success=True, uid=data.get("uid"), deleted=True)


@tool(args_schema=GetDomainConfigInput)
@serialize_pydantic_return
async def get_domain_config(
    api_key: str,
    domain: str,
    team_id: str | None = None,
) -> GetDomainConfigOutput:
    """Get the configuration for a domain in a Vercel account."""
    if not api_key or not api_key.strip():
        return GetDomainConfigOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v6/domains/{domain.strip()}/config",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetDomainConfigOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetDomainConfigOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetDomainConfigOutput(success=False, error=f"Get domain config failed: {exc}")

    return GetDomainConfigOutput(
        success=True,
        configured_by=data.get("configuredBy"),
        accepted_challenges=data.get("acceptedChallenges") or [],
        misconfigured=data.get("misconfigured", False),
        recommended_ipv4=data.get("recommendedIPv4") or [],
        recommended_cname=data.get("recommendedCNAME") or [],
    )


# --- DNS records -----------------------------------------------------------


@tool(args_schema=ListDnsRecordsInput)
@serialize_pydantic_return
async def list_dns_records(
    api_key: str,
    domain: str,
    limit: int | None = None,
    team_id: str | None = None,
) -> ListDnsRecordsOutput:
    """List all DNS records for a domain in a Vercel account."""
    if not api_key or not api_key.strip():
        return ListDnsRecordsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v5/domains/{domain.strip()}/records",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListDnsRecordsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListDnsRecordsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListDnsRecordsOutput(success=False, error=f"List DNS records failed: {exc}")

    records = data.get("records") or []
    return ListDnsRecordsOutput(
        success=True,
        records=[
            DnsRecordItem.model_validate(
                {
                    "id": r.get("id"),
                    "slug": r.get("slug"),
                    "name": r.get("name"),
                    "type": r.get("type"),
                    "value": r.get("value"),
                    "ttl": r.get("ttl"),
                    "mx_priority": r.get("mxPriority"),
                    "priority": r.get("priority"),
                    "creator": r.get("creator"),
                    "created_at": r.get("createdAt"),
                    "updated_at": r.get("updatedAt"),
                    "comment": r.get("comment"),
                }
            )
            for r in records
        ],
        count=len(records),
        has_more=(data.get("pagination") or {}).get("next") is not None,
    )


@tool(args_schema=CreateDnsRecordInput)
@serialize_pydantic_return
async def create_dns_record(
    api_key: str,
    domain: str,
    record_name: str,
    record_type: str,
    value: str,
    ttl: int | None = None,
    mx_priority: int | None = None,
    team_id: str | None = None,
) -> CreateDnsRecordOutput:
    """Create a DNS record for a domain in a Vercel account."""
    if not api_key or not api_key.strip():
        return CreateDnsRecordOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "name": record_name.strip(),
        "type": record_type.strip(),
        "value": value.strip(),
    }
    if ttl is not None:
        body["ttl"] = ttl
    if mx_priority is not None:
        body["mxPriority"] = mx_priority

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/domains/{domain.strip()}/records",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateDnsRecordOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateDnsRecordOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateDnsRecordOutput(success=False, error=f"Create DNS record failed: {exc}")

    return CreateDnsRecordOutput(success=True, uid=data.get("uid"), updated=data.get("updated"))


@tool(args_schema=UpdateDnsRecordInput)
@serialize_pydantic_return
async def update_dns_record(
    api_key: str,
    record_id: str,
    name: str | None = None,
    value: str | None = None,
    type: str | None = None,
    ttl: int | None = None,
    mx_priority: int | None = None,
    comment: str | None = None,
    team_id: str | None = None,
) -> UpdateDnsRecordOutput:
    """Update an existing DNS record for a domain in a Vercel account."""
    if not api_key or not api_key.strip():
        return UpdateDnsRecordOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if name:
        body["name"] = name
    if value:
        body["value"] = value
    if type:
        body["type"] = type
    if ttl is not None:
        body["ttl"] = ttl
    if mx_priority is not None:
        body["mxPriority"] = mx_priority
    if comment:
        body["comment"] = comment

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v1/domains/records/{record_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code != 200:
            return UpdateDnsRecordOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        try:
            data = response.json()
        except Exception:
            data = {}
    except httpx.TimeoutException:
        return UpdateDnsRecordOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateDnsRecordOutput(success=False, error=f"Update DNS record failed: {exc}")

    return UpdateDnsRecordOutput(
        success=True,
        id=data.get("id"),
        name=data.get("name"),
        type=data.get("type"),
        value=data.get("value"),
        creator=data.get("creator"),
        domain=data.get("domain"),
        ttl=data.get("ttl"),
        comment=data.get("comment"),
        record_type=data.get("recordType"),
        created_at=data.get("createdAt"),
    )


@tool(args_schema=DeleteDnsRecordInput)
@serialize_pydantic_return
async def delete_dns_record(
    api_key: str,
    domain: str,
    record_id: str,
    team_id: str | None = None,
) -> DeleteDnsRecordOutput:
    """Delete a DNS record for a domain in a Vercel account."""
    if not api_key or not api_key.strip():
        return DeleteDnsRecordOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v2/domains/{domain.strip()}/records/{record_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return DeleteDnsRecordOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return DeleteDnsRecordOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteDnsRecordOutput(success=False, error=f"Delete DNS record failed: {exc}")

    return DeleteDnsRecordOutput(success=True, deleted=True)


# --- Aliases ---------------------------------------------------------------


@tool(args_schema=ListAliasesInput)
@serialize_pydantic_return
async def list_aliases(
    api_key: str,
    project_id: str | None = None,
    domain: str | None = None,
    limit: int | None = None,
    team_id: str | None = None,
) -> ListAliasesOutput:
    """List aliases for a Vercel project or team."""
    if not api_key or not api_key.strip():
        return ListAliasesOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if project_id:
        params["projectId"] = project_id.strip()
    if domain:
        params["domain"] = domain.strip()
    if limit is not None:
        params["limit"] = limit
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v4/aliases", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListAliasesOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListAliasesOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListAliasesOutput(success=False, error=f"List aliases failed: {exc}")

    aliases = data.get("aliases") or []
    return ListAliasesOutput(
        success=True,
        aliases=[
            AliasItem.model_validate(
                {
                    "uid": a.get("uid"),
                    "alias": a.get("alias"),
                    "deployment_id": a.get("deploymentId"),
                    "project_id": a.get("projectId"),
                    "created_at": a.get("createdAt"),
                    "updated_at": a.get("updatedAt"),
                    "deployment": a.get("deployment"),
                    "redirect": a.get("redirect"),
                    "redirect_status_code": a.get("redirectStatusCode"),
                }
            )
            for a in aliases
        ],
        count=len(aliases),
        has_more=(data.get("pagination") or {}).get("next") is not None,
    )


@tool(args_schema=GetAliasInput)
@serialize_pydantic_return
async def get_alias(
    api_key: str,
    alias_id: str,
    team_id: str | None = None,
) -> GetAliasOutput:
    """Get details about a specific alias by ID or hostname."""
    if not api_key or not api_key.strip():
        return GetAliasOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v4/aliases/{alias_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetAliasOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetAliasOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetAliasOutput(success=False, error=f"Get alias failed: {exc}")

    return GetAliasOutput(
        success=True,
        uid=data.get("uid"),
        alias=data.get("alias"),
        deployment_id=data.get("deploymentId"),
        project_id=data.get("projectId"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        redirect=data.get("redirect"),
        redirect_status_code=data.get("redirectStatusCode"),
        deployment=data.get("deployment"),
    )


@tool(args_schema=CreateAliasInput)
@serialize_pydantic_return
async def create_alias(
    api_key: str,
    deployment_id: str,
    alias: str,
    team_id: str | None = None,
) -> CreateAliasOutput:
    """Assign an alias (domain/subdomain) to a deployment."""
    if not api_key or not api_key.strip():
        return CreateAliasOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v2/deployments/{deployment_id.strip()}/aliases",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json={"alias": alias.strip()},
            )
        if response.status_code not in (200, 201):
            return CreateAliasOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateAliasOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateAliasOutput(success=False, error=f"Create alias failed: {exc}")

    return CreateAliasOutput(
        success=True,
        uid=data.get("uid"),
        alias=data.get("alias"),
        created=data.get("created"),
        old_deployment_id=data.get("oldDeploymentId"),
    )


@tool(args_schema=DeleteAliasInput)
@serialize_pydantic_return
async def delete_alias(
    api_key: str,
    alias_id: str,
    team_id: str | None = None,
) -> DeleteAliasOutput:
    """Delete an alias by its ID."""
    if not api_key or not api_key.strip():
        return DeleteAliasOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v2/aliases/{alias_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return DeleteAliasOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return DeleteAliasOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteAliasOutput(success=False, error=f"Delete alias failed: {exc}")

    return DeleteAliasOutput(success=True, status=data.get("status") or "SUCCESS")


# --- Edge Configs ----------------------------------------------------------


@tool(args_schema=ListEdgeConfigsInput)
@serialize_pydantic_return
async def list_edge_configs(
    api_key: str,
    team_id: str | None = None,
) -> ListEdgeConfigsOutput:
    """List all Edge Config stores for a team."""
    if not api_key or not api_key.strip():
        return ListEdgeConfigsOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/edge-config",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return ListEdgeConfigsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListEdgeConfigsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListEdgeConfigsOutput(success=False, error=f"List Edge Configs failed: {exc}")

    raw = data if isinstance(data, list) else (data.get("edgeConfigs") or [])
    edge_configs = [
        EdgeConfigStore.model_validate(
            {
                "id": ec.get("id"),
                "slug": ec.get("slug"),
                "owner_id": ec.get("ownerId"),
                "digest": ec.get("digest"),
                "created_at": ec.get("createdAt"),
                "updated_at": ec.get("updatedAt"),
                "item_count": ec.get("itemCount"),
                "size_in_bytes": ec.get("sizeInBytes"),
            }
        )
        for ec in raw
    ]
    return ListEdgeConfigsOutput(success=True, edge_configs=edge_configs, count=len(edge_configs))


@tool(args_schema=GetEdgeConfigInput)
@serialize_pydantic_return
async def get_edge_config(
    api_key: str,
    edge_config_id: str,
    team_id: str | None = None,
) -> GetEdgeConfigOutput:
    """Get details about a specific Edge Config store."""
    if not api_key or not api_key.strip():
        return GetEdgeConfigOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/edge-config/{edge_config_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetEdgeConfigOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEdgeConfigOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEdgeConfigOutput(success=False, error=f"Get Edge Config failed: {exc}")

    return GetEdgeConfigOutput(
        success=True,
        id=data.get("id"),
        slug=data.get("slug"),
        owner_id=data.get("ownerId"),
        digest=data.get("digest"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        item_count=data.get("itemCount"),
        size_in_bytes=data.get("sizeInBytes"),
    )


@tool(args_schema=CreateEdgeConfigInput)
@serialize_pydantic_return
async def create_edge_config(
    api_key: str,
    slug: str,
    team_id: str | None = None,
) -> CreateEdgeConfigOutput:
    """Create a new Edge Config store."""
    if not api_key or not api_key.strip():
        return CreateEdgeConfigOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/edge-config",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json={"slug": slug.strip()},
            )
        if response.status_code not in (200, 201):
            return CreateEdgeConfigOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateEdgeConfigOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateEdgeConfigOutput(success=False, error=f"Create Edge Config failed: {exc}")

    return CreateEdgeConfigOutput(
        success=True,
        id=data.get("id"),
        slug=data.get("slug"),
        owner_id=data.get("ownerId"),
        digest=data.get("digest"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        item_count=data.get("itemCount"),
        size_in_bytes=data.get("sizeInBytes"),
    )


@tool(args_schema=DeleteEdgeConfigInput)
@serialize_pydantic_return
async def delete_edge_config(
    api_key: str,
    edge_config_id: str,
    team_id: str | None = None,
) -> DeleteEdgeConfigOutput:
    """Delete an Edge Config store by ID."""
    if not api_key or not api_key.strip():
        return DeleteEdgeConfigOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v1/edge-config/{edge_config_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return DeleteEdgeConfigOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return DeleteEdgeConfigOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteEdgeConfigOutput(success=False, error=f"Delete Edge Config failed: {exc}")

    return DeleteEdgeConfigOutput(success=True, deleted=True)


@tool(args_schema=GetEdgeConfigItemsInput)
@serialize_pydantic_return
async def get_edge_config_items(
    api_key: str,
    edge_config_id: str,
    team_id: str | None = None,
) -> GetEdgeConfigItemsOutput:
    """Get all items in an Edge Config store."""
    if not api_key or not api_key.strip():
        return GetEdgeConfigItemsOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/edge-config/{edge_config_id.strip()}/items",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetEdgeConfigItemsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetEdgeConfigItemsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetEdgeConfigItemsOutput(success=False, error=f"Get Edge Config items failed: {exc}")

    raw = data if isinstance(data, list) else (data.get("items") or [])
    items = [
        EdgeConfigItem.model_validate(
            {
                "key": item.get("key"),
                "value": item.get("value"),
                "description": item.get("description"),
                "edge_config_id": item.get("edgeConfigId"),
                "created_at": item.get("createdAt"),
                "updated_at": item.get("updatedAt"),
            }
        )
        for item in raw
    ]
    return GetEdgeConfigItemsOutput(success=True, items=items, count=len(items))


@tool(args_schema=UpdateEdgeConfigItemsInput)
@serialize_pydantic_return
async def update_edge_config_items(
    api_key: str,
    edge_config_id: str,
    items: list[dict[str, Any]],
    team_id: str | None = None,
) -> UpdateEdgeConfigItemsOutput:
    """Create, update, upsert, or delete items in an Edge Config store."""
    if not api_key or not api_key.strip():
        return UpdateEdgeConfigItemsOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v1/edge-config/{edge_config_id.strip()}/items",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json={"items": items},
            )
        if response.status_code != 200:
            return UpdateEdgeConfigItemsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return UpdateEdgeConfigItemsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateEdgeConfigItemsOutput(
            success=False, error=f"Update Edge Config items failed: {exc}"
        )

    return UpdateEdgeConfigItemsOutput(success=True, status="ok")


# --- Teams & user ----------------------------------------------------------


@tool(args_schema=ListTeamsInput)
@serialize_pydantic_return
async def list_teams(
    api_key: str,
    limit: int | None = None,
    since: int | None = None,
    until: int | None = None,
) -> ListTeamsOutput:
    """List all teams in a Vercel account."""
    if not api_key or not api_key.strip():
        return ListTeamsOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v2/teams", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListTeamsOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTeamsOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTeamsOutput(success=False, error=f"List teams failed: {exc}")

    teams = data.get("teams") or []
    return ListTeamsOutput(
        success=True,
        teams=[
            TeamItem.model_validate(
                {
                    "id": t.get("id"),
                    "slug": t.get("slug"),
                    "name": t.get("name"),
                    "avatar": t.get("avatar"),
                    "description": t.get("description"),
                    "staging_prefix": t.get("stagingPrefix"),
                    "created_at": t.get("createdAt"),
                    "updated_at": t.get("updatedAt"),
                    "creator_id": t.get("creatorId"),
                    "membership": t.get("membership"),
                }
            )
            for t in teams
        ],
        count=len(teams),
        pagination=data.get("pagination"),
    )


@tool(args_schema=GetTeamInput)
@serialize_pydantic_return
async def get_team(
    api_key: str,
    team_id: str,
) -> GetTeamOutput:
    """Get information about a specific Vercel team."""
    if not api_key or not api_key.strip():
        return GetTeamOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v2/teams/{team_id.strip()}", headers=_headers(api_key)
            )
        if response.status_code != 200:
            return GetTeamOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetTeamOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetTeamOutput(success=False, error=f"Get team failed: {exc}")

    return GetTeamOutput(
        success=True,
        id=data.get("id"),
        slug=data.get("slug"),
        name=data.get("name"),
        avatar=data.get("avatar"),
        description=data.get("description"),
        staging_prefix=data.get("stagingPrefix"),
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
        creator_id=data.get("creatorId"),
        membership=data.get("membership"),
    )


@tool(args_schema=ListTeamMembersInput)
@serialize_pydantic_return
async def list_team_members(
    api_key: str,
    team_id: str,
    limit: int | None = None,
    role: str | None = None,
    since: int | None = None,
    until: int | None = None,
    search: str | None = None,
) -> ListTeamMembersOutput:
    """List all members of a Vercel team."""
    if not api_key or not api_key.strip():
        return ListTeamMembersOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if limit is not None:
        params["limit"] = limit
    if role:
        params["role"] = role.strip()
    if since is not None:
        params["since"] = since
    if until is not None:
        params["until"] = until
    if search:
        params["search"] = search.strip()

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v3/teams/{team_id.strip()}/members",
                headers=_headers(api_key),
                params=params,
            )
        if response.status_code != 200:
            return ListTeamMembersOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListTeamMembersOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListTeamMembersOutput(success=False, error=f"List team members failed: {exc}")

    members = data.get("members") or []
    return ListTeamMembersOutput(
        success=True,
        members=[
            TeamMember.model_validate(
                {
                    "uid": m.get("uid"),
                    "email": m.get("email"),
                    "username": m.get("username"),
                    "name": m.get("name"),
                    "avatar": m.get("avatar"),
                    "role": m.get("role"),
                    "confirmed": m.get("confirmed", False),
                    "created_at": m.get("createdAt"),
                    "access_requested_at": m.get("accessRequestedAt"),
                    "is_enterprise_managed": m.get("isEnterpriseManaged"),
                    "joined_from": m.get("joinedFrom"),
                }
            )
            for m in members
        ],
        count=len(members),
        pagination=data.get("pagination"),
    )


@tool(args_schema=GetUserInput)
@serialize_pydantic_return
async def get_user(api_key: str) -> GetUserOutput:
    """Get information about the authenticated Vercel user."""
    if not api_key or not api_key.strip():
        return GetUserOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(f"{_BASE_URL}/v2/user", headers=_headers(api_key))
        if response.status_code != 200:
            return GetUserOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetUserOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetUserOutput(success=False, error=f"Get user failed: {exc}")

    d = data.get("user") or data
    return GetUserOutput(
        success=True,
        id=d.get("id"),
        email=d.get("email"),
        username=d.get("username"),
        name=d.get("name"),
        avatar=d.get("avatar"),
        default_team_id=d.get("defaultTeamId"),
        created_at=d.get("createdAt"),
        staging_prefix=d.get("stagingPrefix"),
        soft_block=d.get("softBlock"),
        has_trial_available=d.get("hasTrialAvailable"),
    )


# --- Webhooks --------------------------------------------------------------


@tool(args_schema=ListWebhooksInput)
@serialize_pydantic_return
async def list_webhooks(
    api_key: str,
    project_id: str | None = None,
    team_id: str | None = None,
) -> ListWebhooksOutput:
    """List webhooks for a Vercel project or team."""
    if not api_key or not api_key.strip():
        return ListWebhooksOutput(success=False, error=_EMPTY_KEY_ERROR)

    params: dict[str, Any] = {}
    if project_id:
        params["projectId"] = project_id.strip()
    params.update(_team_params(team_id))

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/webhooks", headers=_headers(api_key), params=params
            )
        if response.status_code != 200:
            return ListWebhooksOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListWebhooksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListWebhooksOutput(success=False, error=f"List webhooks failed: {exc}")

    raw = data if isinstance(data, list) else []
    webhooks = [
        WebhookItem.model_validate(
            {
                "id": w.get("id"),
                "url": w.get("url"),
                "events": w.get("events") or [],
                "owner_id": w.get("ownerId"),
                "project_ids": w.get("projectIds") or [],
                "projects_metadata": w.get("projectsMetadata") or [],
                "created_at": w.get("createdAt"),
                "updated_at": w.get("updatedAt"),
            }
        )
        for w in raw
    ]
    return ListWebhooksOutput(success=True, webhooks=webhooks, count=len(webhooks))


@tool(args_schema=GetWebhookInput)
@serialize_pydantic_return
async def get_webhook(
    api_key: str,
    webhook_id: str,
    team_id: str | None = None,
) -> GetWebhookOutput:
    """Get details about a specific Vercel webhook."""
    if not api_key or not api_key.strip():
        return GetWebhookOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/webhooks/{webhook_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetWebhookOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetWebhookOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetWebhookOutput(success=False, error=f"Get webhook failed: {exc}")

    return GetWebhookOutput(
        success=True,
        id=data.get("id"),
        url=data.get("url"),
        events=data.get("events") or [],
        owner_id=data.get("ownerId"),
        project_ids=data.get("projectIds") or [],
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=CreateWebhookInput)
@serialize_pydantic_return
async def create_webhook(
    api_key: str,
    url: str,
    events: str,
    project_ids: str | None = None,
    team_id: str | None = None,
) -> CreateWebhookOutput:
    """Create a new webhook for a Vercel team or account."""
    if not api_key or not api_key.strip():
        return CreateWebhookOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {
        "url": url.strip(),
        "events": [e.strip() for e in events.split(",")],
    }
    if project_ids:
        body["projectIds"] = [p.strip() for p in project_ids.split(",")]

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/webhooks",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CreateWebhookOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CreateWebhookOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CreateWebhookOutput(success=False, error=f"Create webhook failed: {exc}")

    return CreateWebhookOutput(
        success=True,
        id=data.get("id"),
        url=data.get("url"),
        secret=data.get("secret"),
        events=data.get("events") or [],
        owner_id=data.get("ownerId"),
        project_ids=data.get("projectIds") or [],
        created_at=data.get("createdAt"),
        updated_at=data.get("updatedAt"),
    )


@tool(args_schema=DeleteWebhookInput)
@serialize_pydantic_return
async def delete_webhook(
    api_key: str,
    webhook_id: str,
    team_id: str | None = None,
) -> DeleteWebhookOutput:
    """Delete a webhook from a Vercel team or account."""
    if not api_key or not api_key.strip():
        return DeleteWebhookOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.delete(
                f"{_BASE_URL}/v1/webhooks/{webhook_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 204):
            return DeleteWebhookOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return DeleteWebhookOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return DeleteWebhookOutput(success=False, error=f"Delete webhook failed: {exc}")

    return DeleteWebhookOutput(success=True, deleted=True)


# --- Checks ----------------------------------------------------------------


def _parse_check(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": data.get("id"),
        "name": data.get("name"),
        "status": data.get("status") or "registered",
        "conclusion": data.get("conclusion"),
        "blocking": data.get("blocking", False),
        "deployment_id": data.get("deploymentId"),
        "integration_id": data.get("integrationId"),
        "external_id": data.get("externalId"),
        "details_url": data.get("detailsUrl"),
        "path": data.get("path"),
        "rerequestable": data.get("rerequestable", False),
        "created_at": data.get("createdAt"),
        "updated_at": data.get("updatedAt"),
        "started_at": data.get("startedAt"),
        "completed_at": data.get("completedAt"),
        "output": data.get("output"),
    }


@tool(args_schema=CreateCheckInput)
@serialize_pydantic_return
async def create_check(
    api_key: str,
    deployment_id: str,
    name: str,
    blocking: bool,
    path: str | None = None,
    details_url: str | None = None,
    external_id: str | None = None,
    rerequestable: bool | None = None,
    team_id: str | None = None,
) -> CheckOutput:
    """Create a new deployment check."""
    if not api_key or not api_key.strip():
        return CheckOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {"name": name.strip(), "blocking": blocking}
    if path:
        body["path"] = path
    if details_url:
        body["detailsUrl"] = details_url
    if external_id:
        body["externalId"] = external_id
    if rerequestable is not None:
        body["rerequestable"] = rerequestable

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/deployments/{deployment_id.strip()}/checks",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code not in (200, 201):
            return CheckOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return CheckOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return CheckOutput(success=False, error=f"Create check failed: {exc}")

    return CheckOutput(success=True, **_parse_check(data))


@tool(args_schema=GetCheckInput)
@serialize_pydantic_return
async def get_check(
    api_key: str,
    deployment_id: str,
    check_id: str,
    team_id: str | None = None,
) -> GetCheckOutput:
    """Get details of a specific deployment check."""
    if not api_key or not api_key.strip():
        return GetCheckOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/deployments/{deployment_id.strip()}/checks/{check_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return GetCheckOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return GetCheckOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return GetCheckOutput(success=False, error=f"Get check failed: {exc}")

    return GetCheckOutput(success=True, **_parse_check(data))


@tool(args_schema=ListChecksInput)
@serialize_pydantic_return
async def list_checks(
    api_key: str,
    deployment_id: str,
    team_id: str | None = None,
) -> ListChecksOutput:
    """List all checks for a deployment."""
    if not api_key or not api_key.strip():
        return ListChecksOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.get(
                f"{_BASE_URL}/v1/deployments/{deployment_id.strip()}/checks",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code != 200:
            return ListChecksOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return ListChecksOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return ListChecksOutput(success=False, error=f"List checks failed: {exc}")

    checks = data.get("checks") or []
    return ListChecksOutput(
        success=True,
        checks=[CheckItem.model_validate(_parse_check(c)) for c in checks],
        count=len(checks),
    )


@tool(args_schema=UpdateCheckInput)
@serialize_pydantic_return
async def update_check(
    api_key: str,
    deployment_id: str,
    check_id: str,
    name: str | None = None,
    status: str | None = None,
    conclusion: str | None = None,
    details_url: str | None = None,
    external_id: str | None = None,
    path: str | None = None,
    output: dict[str, Any] | None = None,
    team_id: str | None = None,
) -> UpdateCheckOutput:
    """Update an existing deployment check."""
    if not api_key or not api_key.strip():
        return UpdateCheckOutput(success=False, error=_EMPTY_KEY_ERROR)

    body: dict[str, Any] = {}
    if name:
        body["name"] = name.strip()
    if status:
        body["status"] = status
    if conclusion:
        body["conclusion"] = conclusion
    if details_url:
        body["detailsUrl"] = details_url
    if external_id:
        body["externalId"] = external_id
    if path:
        body["path"] = path
    if output is not None:
        body["output"] = output

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.patch(
                f"{_BASE_URL}/v1/deployments/{deployment_id.strip()}/checks/{check_id.strip()}",
                headers=_headers(api_key),
                params=_team_params(team_id),
                json=body,
            )
        if response.status_code != 200:
            return UpdateCheckOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
        data = response.json()
    except httpx.TimeoutException:
        return UpdateCheckOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return UpdateCheckOutput(success=False, error=f"Update check failed: {exc}")

    return UpdateCheckOutput(success=True, **_parse_check(data))


@tool(args_schema=RerequestCheckInput)
@serialize_pydantic_return
async def rerequest_check(
    api_key: str,
    deployment_id: str,
    check_id: str,
    team_id: str | None = None,
) -> RerequestCheckOutput:
    """Rerequest a deployment check."""
    if not api_key or not api_key.strip():
        return RerequestCheckOutput(success=False, error=_EMPTY_KEY_ERROR)

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            response = await client.post(
                f"{_BASE_URL}/v1/deployments/{deployment_id.strip()}/checks/{check_id.strip()}/rerequest",
                headers=_headers(api_key),
                params=_team_params(team_id),
            )
        if response.status_code not in (200, 201):
            return RerequestCheckOutput(
                success=False, error=f"Vercel API error ({response.status_code}): {response.text}"
            )
    except httpx.TimeoutException:
        return RerequestCheckOutput(success=False, error="Request timed out.")
    except Exception as exc:
        return RerequestCheckOutput(success=False, error=f"Rerequest check failed: {exc}")

    return RerequestCheckOutput(success=True, rerequested=True)
