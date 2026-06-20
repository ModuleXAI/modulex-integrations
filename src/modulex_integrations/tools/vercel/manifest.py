"""Vercel integration manifest.

Vercel exposes a single key-based credential method: a personal Vercel
Access Token sent as ``Authorization: Bearer <token>``. The runtime
injects the token into each tool's ``api_key`` parameter.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


_TEAM_ID = ParameterDef(type="string", description="Team ID to scope the request")


manifest = IntegrationManifest(
    name="vercel",
    display_name="Vercel",
    description=(
        "Integrate with Vercel to manage deployments, projects, domains, DNS "
        "records, environment variables, aliases, edge configs, teams, "
        "webhooks, and deployment checks."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:vercel-themed",
    app_url="https://vercel.com",
    categories=["Developer Tools & Infrastructure", "Cloud Infrastructure", "tools"],
    actions=[
        # --- Deployments ---------------------------------------------------
        ActionDefinition(
            name="list_deployments",
            description="List deployments for a Vercel project or team.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Filter deployments by project ID or name"
                ),
                "target": ParameterDef(
                    type="string", description="Filter by environment: production or staging"
                ),
                "state": ParameterDef(
                    type="string",
                    description=(
                        "Filter by state: BUILDING, ERROR, INITIALIZING, QUEUED, "
                        "READY, CANCELED, BLOCKED"
                    ),
                ),
                "app": ParameterDef(type="string", description="Filter by deployment name"),
                "since": ParameterDef(
                    type="integer", description="Get deployments created after this timestamp"
                ),
                "until": ParameterDef(
                    type="integer", description="Get deployments created before this timestamp"
                ),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of deployments to return"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_deployment",
            description="Get details of a specific Vercel deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="The unique deployment identifier or hostname",
                    required=True,
                ),
                "with_git_repo_info": ParameterDef(
                    type="string", description="Whether to add gitRepo information (true/false)"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_deployment",
            description="Create a new deployment or redeploy an existing one.",
            parameters={
                "name": ParameterDef(
                    type="string", description="Project name for the deployment", required=True
                ),
                "project": ParameterDef(
                    type="string", description="Project ID (overrides name for project lookup)"
                ),
                "deployment_id": ParameterDef(
                    type="string", description="Existing deployment ID to redeploy"
                ),
                "target": ParameterDef(
                    type="string",
                    description="Target environment: production, staging, or a custom environment",
                ),
                "git_source": ParameterDef(
                    type="object",
                    description=(
                        "Git Repository source to deploy "
                        '(e.g. {"type":"github","repo":"owner/repo","ref":"main"})'
                    ),
                ),
                "force_new": ParameterDef(
                    type="string",
                    description="Force a new deployment even if a similar one exists (0 or 1)",
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="cancel_deployment",
            description="Cancel a running Vercel deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="The deployment ID to cancel", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_deployment",
            description="Delete a Vercel deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="The deployment ID or URL to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_deployment_events",
            description="Get build and runtime events for a Vercel deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="The unique deployment identifier or hostname",
                    required=True,
                ),
                "direction": ParameterDef(
                    type="string", description="Order of events by timestamp: backward or forward"
                ),
                "follow": ParameterDef(
                    type="integer", description="When set to 1, returns live events as they happen"
                ),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of events to return (-1 for all)"
                ),
                "since": ParameterDef(
                    type="integer", description="Timestamp to start pulling build logs from"
                ),
                "until": ParameterDef(
                    type="integer", description="Timestamp to stop pulling build logs at"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="list_deployment_files",
            description="List file-tree metadata for a Vercel deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="The deployment ID to list files for", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="promote_deployment",
            description="Promote a deployment to production for the given project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "deployment_id": ParameterDef(
                    type="string",
                    description="The ID of the deployment to promote to production",
                    required=True,
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Projects ------------------------------------------------------
        ActionDefinition(
            name="list_projects",
            description="List all projects in a Vercel team or account.",
            parameters={
                "search": ParameterDef(type="string", description="Search projects by name"),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of projects to return"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_project",
            description="Get details of a specific Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_project",
            description="Create a new Vercel project.",
            parameters={
                "name": ParameterDef(type="string", description="Project name", required=True),
                "framework": ParameterDef(
                    type="string", description="Project framework (e.g. nextjs, remix, vite)"
                ),
                "git_repository": ParameterDef(
                    type="object",
                    description="Git repository connection object with type and repo",
                ),
                "build_command": ParameterDef(type="string", description="Custom build command"),
                "output_directory": ParameterDef(
                    type="string", description="Custom output directory"
                ),
                "install_command": ParameterDef(
                    type="string", description="Custom install command"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="update_project",
            description="Update an existing Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "name": ParameterDef(type="string", description="New project name"),
                "framework": ParameterDef(
                    type="string", description="Project framework (e.g. nextjs, remix, vite)"
                ),
                "build_command": ParameterDef(type="string", description="Custom build command"),
                "output_directory": ParameterDef(
                    type="string", description="Custom output directory"
                ),
                "install_command": ParameterDef(
                    type="string", description="Custom install command"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_project",
            description="Delete a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="pause_project",
            description="Pause a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="unpause_project",
            description="Unpause a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Project domains ----------------------------------------------
        ActionDefinition(
            name="list_project_domains",
            description="List all domains for a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "team_id": _TEAM_ID,
                "limit": ParameterDef(
                    type="integer", description="Maximum number of domains to return"
                ),
            },
        ),
        ActionDefinition(
            name="add_project_domain",
            description="Add a domain to a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "domain": ParameterDef(
                    type="string", description="Domain name to add", required=True
                ),
                "redirect": ParameterDef(type="string", description="Target domain for redirect"),
                "redirect_status_code": ParameterDef(
                    type="integer", description="HTTP status code for redirect (301, 302, 307, 308)"
                ),
                "git_branch": ParameterDef(
                    type="string", description="Git branch to link the domain to"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="update_project_domain",
            description="Update a project domain's configuration on Vercel.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "domain": ParameterDef(
                    type="string", description="Domain name to update", required=True
                ),
                "redirect": ParameterDef(
                    type="string", description="Target destination domain for redirect"
                ),
                "redirect_status_code": ParameterDef(
                    type="integer", description="HTTP status code for redirect (301, 302, 307, 308)"
                ),
                "git_branch": ParameterDef(
                    type="string", description="Git branch to link the domain to"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="verify_project_domain",
            description="Verify a Vercel project domain by checking its verification challenge.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "domain": ParameterDef(
                    type="string", description="Domain name to verify", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="remove_project_domain",
            description="Remove a domain from a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "domain": ParameterDef(
                    type="string", description="Domain name to remove", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Environment variables ----------------------------------------
        ActionDefinition(
            name="get_env_vars",
            description="Retrieve environment variables for a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_env_var",
            description="Create an environment variable for a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "key": ParameterDef(
                    type="string", description="Environment variable name", required=True
                ),
                "value": ParameterDef(
                    type="string", description="Environment variable value", required=True
                ),
                "target": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated target environments "
                        "(production, preview, development)"
                    ),
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Variable type: system, encrypted, plain, or sensitive",
                    default="plain",
                ),
                "git_branch": ParameterDef(
                    type="string",
                    description="Git branch to associate (requires target to include preview)",
                ),
                "comment": ParameterDef(
                    type="string", description="Comment to add context (max 500 characters)"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="update_env_var",
            description="Update an environment variable for a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "env_id": ParameterDef(
                    type="string", description="Environment variable ID to update", required=True
                ),
                "key": ParameterDef(type="string", description="New variable name"),
                "value": ParameterDef(type="string", description="New variable value"),
                "target": ParameterDef(
                    type="string",
                    description=(
                        "Comma-separated target environments "
                        "(production, preview, development)"
                    ),
                ),
                "type": ParameterDef(
                    type="string",
                    description="Variable type: system, encrypted, plain, or sensitive",
                ),
                "git_branch": ParameterDef(
                    type="string",
                    description="Git branch to associate (requires target to include preview)",
                ),
                "comment": ParameterDef(
                    type="string", description="Comment to add context (max 500 characters)"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_env_var",
            description="Delete an environment variable from a Vercel project.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Project ID or name", required=True
                ),
                "env_id": ParameterDef(
                    type="string", description="Environment variable ID to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Account domains ----------------------------------------------
        ActionDefinition(
            name="list_domains",
            description="List all domains in a Vercel account or team.",
            parameters={
                "limit": ParameterDef(
                    type="integer", description="Maximum number of domains to return"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_domain",
            description="Get information about a specific domain in a Vercel account.",
            parameters={
                "domain": ParameterDef(
                    type="string", description="The domain name to retrieve", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="add_domain",
            description="Add a new domain to a Vercel account or team.",
            parameters={
                "name": ParameterDef(
                    type="string", description="The domain name to add", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_domain",
            description="Delete a domain from a Vercel account or team.",
            parameters={
                "domain": ParameterDef(
                    type="string", description="The domain name to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_domain_config",
            description="Get the configuration for a domain in a Vercel account.",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain name to get configuration for",
                    required=True,
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- DNS records ---------------------------------------------------
        ActionDefinition(
            name="list_dns_records",
            description="List all DNS records for a domain in a Vercel account.",
            parameters={
                "domain": ParameterDef(
                    type="string", description="The domain name to list records for", required=True
                ),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of records to return"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_dns_record",
            description="Create a DNS record for a domain in a Vercel account.",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain name to create the record for",
                    required=True,
                ),
                "record_name": ParameterDef(
                    type="string", description="The subdomain or record name", required=True
                ),
                "record_type": ParameterDef(
                    type="string",
                    description=(
                        "DNS record type (A, AAAA, ALIAS, CAA, CNAME, HTTPS, MX, SRV, TXT, NS)"
                    ),
                    required=True,
                ),
                "value": ParameterDef(
                    type="string", description="The value of the DNS record", required=True
                ),
                "ttl": ParameterDef(type="integer", description="Time to live in seconds"),
                "mx_priority": ParameterDef(type="integer", description="Priority for MX records"),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="update_dns_record",
            description="Update an existing DNS record for a domain in a Vercel account.",
            parameters={
                "record_id": ParameterDef(
                    type="string", description="The ID of the DNS record to update", required=True
                ),
                "name": ParameterDef(type="string", description="The name of the DNS record"),
                "value": ParameterDef(type="string", description="The value of the DNS record"),
                "type": ParameterDef(
                    type="string",
                    description=(
                        "DNS record type (A, AAAA, ALIAS, CAA, CNAME, HTTPS, MX, SRV, TXT, NS)"
                    ),
                ),
                "ttl": ParameterDef(
                    type="integer", description="Time to live in seconds (60 to 2147483647)"
                ),
                "mx_priority": ParameterDef(type="integer", description="Priority for MX records"),
                "comment": ParameterDef(
                    type="string", description="Comment to add context (max 500 characters)"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_dns_record",
            description="Delete a DNS record for a domain in a Vercel account.",
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="The domain name the record belongs to", required=True,
                ),
                "record_id": ParameterDef(
                    type="string", description="The ID of the DNS record to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Aliases -------------------------------------------------------
        ActionDefinition(
            name="list_aliases",
            description="List aliases for a Vercel project or team.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Filter aliases by project ID"
                ),
                "domain": ParameterDef(type="string", description="Filter aliases by domain"),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of aliases to return"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_alias",
            description="Get details about a specific alias by ID or hostname.",
            parameters={
                "alias_id": ParameterDef(
                    type="string", description="Alias ID or hostname to look up", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_alias",
            description="Assign an alias (domain/subdomain) to a deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="Deployment ID to assign the alias to", required=True
                ),
                "alias": ParameterDef(
                    type="string",
                    description="The domain or subdomain to assign as an alias",
                    required=True,
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_alias",
            description="Delete an alias by its ID.",
            parameters={
                "alias_id": ParameterDef(
                    type="string", description="Alias ID to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Edge Configs --------------------------------------------------
        ActionDefinition(
            name="list_edge_configs",
            description="List all Edge Config stores for a team.",
            parameters={"team_id": _TEAM_ID},
        ),
        ActionDefinition(
            name="get_edge_config",
            description="Get details about a specific Edge Config store.",
            parameters={
                "edge_config_id": ParameterDef(
                    type="string", description="Edge Config ID to look up", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_edge_config",
            description="Create a new Edge Config store.",
            parameters={
                "slug": ParameterDef(
                    type="string",
                    description="The name/slug for the new Edge Config", required=True,
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_edge_config_items",
            description="Get all items in an Edge Config store.",
            parameters={
                "edge_config_id": ParameterDef(
                    type="string", description="Edge Config ID to get items from", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="update_edge_config_items",
            description="Create, update, upsert, or delete items in an Edge Config store.",
            parameters={
                "edge_config_id": ParameterDef(
                    type="string", description="Edge Config ID to update items in", required=True
                ),
                "items": ParameterDef(
                    type="array",
                    description=(
                        "Array of operations: "
                        '[{"operation": "create|update|upsert|delete", "key": "...", '
                        '"value": ...}]'
                    ),
                    required=True,
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_edge_config",
            description="Delete an Edge Config store by ID.",
            parameters={
                "edge_config_id": ParameterDef(
                    type="string", description="Edge Config ID to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Webhooks ------------------------------------------------------
        ActionDefinition(
            name="list_webhooks",
            description="List webhooks for a Vercel project or team.",
            parameters={
                "project_id": ParameterDef(
                    type="string", description="Filter webhooks by project ID"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_webhook",
            description="Get details about a specific Vercel webhook.",
            parameters={
                "webhook_id": ParameterDef(
                    type="string", description="Webhook ID to look up", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="create_webhook",
            description="Create a new webhook for a Vercel team or account.",
            parameters={
                "url": ParameterDef(
                    type="string", description="Webhook URL (must be https)", required=True
                ),
                "events": ParameterDef(
                    type="string",
                    description="Comma-separated event names to subscribe to",
                    required=True,
                ),
                "project_ids": ParameterDef(
                    type="string",
                    description="Comma-separated project IDs to scope the webhook to",
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="delete_webhook",
            description="Delete a webhook from a Vercel team or account.",
            parameters={
                "webhook_id": ParameterDef(
                    type="string", description="The webhook ID to delete", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Checks --------------------------------------------------------
        ActionDefinition(
            name="create_check",
            description="Create a new deployment check.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="Deployment ID to create the check for", required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name of the check (max 100 characters)", required=True,
                ),
                "blocking": ParameterDef(
                    type="boolean",
                    description="Whether the check blocks the deployment",
                    required=True,
                ),
                "path": ParameterDef(type="string", description="Page path being checked"),
                "details_url": ParameterDef(
                    type="string", description="URL with details about the check"
                ),
                "external_id": ParameterDef(
                    type="string", description="External identifier for the check"
                ),
                "rerequestable": ParameterDef(
                    type="boolean", description="Whether the check can be rerequested"
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="get_check",
            description="Get details of a specific deployment check.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="Deployment ID the check belongs to", required=True
                ),
                "check_id": ParameterDef(
                    type="string", description="Check ID to retrieve", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="list_checks",
            description="List all checks for a deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="Deployment ID to list checks for", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="update_check",
            description="Update an existing deployment check.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="Deployment ID the check belongs to", required=True
                ),
                "check_id": ParameterDef(
                    type="string", description="Check ID to update", required=True
                ),
                "name": ParameterDef(type="string", description="Updated name of the check"),
                "status": ParameterDef(
                    type="string", description="Updated status: running or completed"
                ),
                "conclusion": ParameterDef(
                    type="string",
                    description=(
                        "Check conclusion: canceled, failed, neutral, succeeded, or skipped"
                    ),
                ),
                "details_url": ParameterDef(
                    type="string", description="URL with details about the check"
                ),
                "external_id": ParameterDef(
                    type="string", description="External identifier for the check"
                ),
                "path": ParameterDef(type="string", description="Page path being checked"),
                "output": ParameterDef(type="object", description="Check output metrics object"),
                "team_id": _TEAM_ID,
            },
        ),
        ActionDefinition(
            name="rerequest_check",
            description="Rerequest a deployment check.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string", description="Deployment ID the check belongs to", required=True
                ),
                "check_id": ParameterDef(
                    type="string", description="Check ID to rerequest", required=True
                ),
                "team_id": _TEAM_ID,
            },
        ),
        # --- Teams & user --------------------------------------------------
        ActionDefinition(
            name="list_teams",
            description="List all teams in a Vercel account.",
            parameters={
                "limit": ParameterDef(
                    type="integer", description="Maximum number of teams to return"
                ),
                "since": ParameterDef(
                    type="integer",
                    description="Only include teams created since this timestamp (ms)",
                ),
                "until": ParameterDef(
                    type="integer",
                    description="Only include teams created until this timestamp (ms)",
                ),
            },
        ),
        ActionDefinition(
            name="get_team",
            description="Get information about a specific Vercel team.",
            parameters={
                "team_id": ParameterDef(
                    type="string", description="The team ID to retrieve", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_team_members",
            description="List all members of a Vercel team.",
            parameters={
                "team_id": ParameterDef(
                    type="string", description="The team ID to list members for", required=True
                ),
                "limit": ParameterDef(
                    type="integer", description="Maximum number of members to return"
                ),
                "role": ParameterDef(
                    type="string",
                    description=(
                        "Filter by role (OWNER, MEMBER, DEVELOPER, SECURITY, BILLING, "
                        "VIEWER, CONTRIBUTOR)"
                    ),
                ),
                "since": ParameterDef(
                    type="integer",
                    description="Only include members added since this timestamp (ms)",
                ),
                "until": ParameterDef(
                    type="integer",
                    description="Only include members added until this timestamp (ms)",
                ),
                "search": ParameterDef(
                    type="string", description="Search members by name, username, and email"
                ),
            },
        ),
        ActionDefinition(
            name="get_user",
            description="Get information about the authenticated Vercel user.",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Vercel Access Token",
            setup_instructions=[
                "Sign in at https://vercel.com and open Account Settings → Tokens",
                "Click 'Create Token', enter a name and (recommended) an expiration",
                "Copy the generated token (it is shown only once)",
                "Paste the token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="VERCEL_API_KEY",
                    display_name="Vercel Access Token",
                    description="Your Vercel Access Token from the Account Tokens page",
                    required=True,
                    sensitive=True,
                    about_url="https://vercel.com/account/tokens",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.vercel.com/v2/user",
                method="GET",
                headers={"Authorization": "Bearer {api_key}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["user"],
                ),
                cost_level="free",
                description="Validates the access token by fetching the authenticated user",
            ),
        ),
    ],
)
