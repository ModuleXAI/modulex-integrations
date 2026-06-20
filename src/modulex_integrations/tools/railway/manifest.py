"""Railway integration manifest.

Railway exposes a single public GraphQL endpoint
(``https://backboard.railway.com/graphql/v2``). Authentication is via an
API token; the ``token_type`` action parameter selects the header
(account/workspace/OAuth tokens use ``Authorization: Bearer``, project
tokens use ``Project-Access-Token``). Only the bring-your-own-key
``api_key`` schema is shipped.
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


_TOKEN_TYPE = ParameterDef(
    type="string",
    description=(
        'Railway token type. Use "account" for account, workspace, or OAuth '
        'tokens, or "project" for project tokens.'
    ),
    default="account",
)


manifest = IntegrationManifest(
    name="railway",
    display_name="Railway",
    description=(
        "Integrate Railway into workflows to list projects, manage services and "
        "environments, monitor deployments, trigger and roll back service "
        "deployments, and manage environment variables."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:railway-themed",
    app_url="https://railway.com",
    categories=["Developer Tools & Infrastructure", "cloud", "ci-cd"],
    actions=[
        ActionDefinition(
            name="list_projects",
            description="List Railway projects visible to the provided token.",
            parameters={
                "token_type": _TOKEN_TYPE,
                "workspace_id": ParameterDef(
                    type="string",
                    description="Workspace ID to list projects from",
                ),
                "first": ParameterDef(
                    type="integer",
                    description="Maximum number of projects to return",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Cursor for pagination",
                ),
            },
        ),
        ActionDefinition(
            name="get_project",
            description="Get a Railway project with its services and environments.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="create_project",
            description="Create a Railway project.",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Project name",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "description": ParameterDef(
                    type="string",
                    description="Project description",
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="Workspace ID to create the project in",
                ),
                "is_public": ParameterDef(
                    type="boolean",
                    description="Whether the project should be publicly visible",
                ),
                "default_environment_name": ParameterDef(
                    type="string",
                    description="Name for the default environment",
                ),
                "pr_deploys": ParameterDef(
                    type="boolean",
                    description="Whether to enable pull request deploys",
                ),
            },
        ),
        ActionDefinition(
            name="update_project",
            description="Update a Railway project name or description.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "name": ParameterDef(
                    type="string",
                    description="Updated project name",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Updated project description",
                ),
                "is_public": ParameterDef(
                    type="boolean",
                    description="Whether the project should be publicly visible",
                ),
                "pr_deploys": ParameterDef(
                    type="boolean",
                    description="Whether to enable pull request deploy environments",
                ),
            },
        ),
        ActionDefinition(
            name="delete_project",
            description="Delete a Railway project.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="transfer_project",
            description="Transfer a Railway project to another workspace.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="Destination workspace ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="list_project_members",
            description="List members for a Railway project.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="create_environment",
            description="Create a Railway project environment.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Environment name",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "source_environment_id": ParameterDef(
                    type="string",
                    description="Environment ID to clone from",
                ),
                "ephemeral": ParameterDef(
                    type="boolean",
                    description="Whether the environment is ephemeral",
                ),
                "skip_initial_deploys": ParameterDef(
                    type="boolean",
                    description="Whether to skip initial deploys for the environment",
                ),
                "stage_initial_changes": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether to stage initial changes instead of applying them immediately"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="delete_environment",
            description="Delete a Railway project environment.",
            parameters={
                "environment_id": ParameterDef(
                    type="string",
                    description="Railway environment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="create_service",
            description="Create a Railway service from a GitHub repo or Docker image.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Service name",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "repo": ParameterDef(
                    type="string",
                    description="GitHub repository in owner/name format to deploy from",
                ),
                "image": ParameterDef(
                    type="string",
                    description="Docker image to deploy, for example redis:7-alpine",
                ),
                "branch": ParameterDef(
                    type="string",
                    description="Git branch to deploy when using a repository source",
                ),
            },
        ),
        ActionDefinition(
            name="delete_service",
            description="Delete a Railway service and all of its deployments.",
            parameters={
                "service_id": ParameterDef(
                    type="string",
                    description="Railway service ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="list_deployments",
            description="List deployments for a Railway service in an environment.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "service_id": ParameterDef(
                    type="string",
                    description="Railway service ID",
                    required=True,
                ),
                "environment_id": ParameterDef(
                    type="string",
                    description="Railway environment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "first": ParameterDef(
                    type="integer",
                    description="Maximum number of deployments to return",
                ),
                "after": ParameterDef(
                    type="string",
                    description="Cursor for pagination",
                ),
            },
        ),
        ActionDefinition(
            name="get_deployment",
            description="Get details for a single Railway deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="Railway deployment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="deploy_service",
            description="Trigger a deployment for a Railway service in an environment.",
            parameters={
                "service_id": ParameterDef(
                    type="string",
                    description="Railway service ID",
                    required=True,
                ),
                "environment_id": ParameterDef(
                    type="string",
                    description="Railway environment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "commit_sha": ParameterDef(
                    type="string",
                    description="Specific Git commit SHA to deploy",
                ),
            },
        ),
        ActionDefinition(
            name="restart_deployment",
            description="Restart a running Railway deployment without rebuilding.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="Railway deployment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="rollback_deployment",
            description="Roll a Railway service back to a previous deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="Railway deployment ID to roll back to (must have canRollback)",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
            },
        ),
        ActionDefinition(
            name="get_deployment_logs",
            description="Retrieve runtime logs for a Railway deployment.",
            parameters={
                "deployment_id": ParameterDef(
                    type="string",
                    description="Railway deployment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of log lines to return",
                ),
            },
        ),
        ActionDefinition(
            name="list_variables",
            description=(
                "List Railway environment variables for a service or shared environment."
            ),
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "environment_id": ParameterDef(
                    type="string",
                    description="Railway environment ID",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "service_id": ParameterDef(
                    type="string",
                    description="Railway service ID. Omit for shared environment variables.",
                ),
            },
        ),
        ActionDefinition(
            name="upsert_variable",
            description="Create or update a Railway environment variable.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "environment_id": ParameterDef(
                    type="string",
                    description="Railway environment ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Variable name",
                    required=True,
                ),
                "value": ParameterDef(
                    type="string",
                    description="Variable value",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "service_id": ParameterDef(
                    type="string",
                    description=(
                        "Railway service ID. Omit to create or update a shared variable."
                    ),
                ),
                "skip_deploys": ParameterDef(
                    type="boolean",
                    description=(
                        "Whether to skip automatic redeploys after changing the variable"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="delete_variable",
            description="Delete a Railway environment variable.",
            parameters={
                "project_id": ParameterDef(
                    type="string",
                    description="Railway project ID",
                    required=True,
                ),
                "environment_id": ParameterDef(
                    type="string",
                    description="Railway environment ID",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Variable name to delete",
                    required=True,
                ),
                "token_type": _TOKEN_TYPE,
                "service_id": ParameterDef(
                    type="string",
                    description="Railway service ID. Omit to delete a shared variable.",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Token Authentication",
            description="Authenticate using your Railway API token",
            setup_instructions=[
                "Sign in at https://railway.com and open your account settings",
                "Go to the 'Tokens' section under Account Settings",
                "Create a new token (account, workspace, or project scope)",
                "Paste the token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="RAILWAY_API_TOKEN",
                    display_name="Railway API Token",
                    description="Your Railway API token from account settings",
                    required=True,
                    sensitive=True,
                    about_url="https://docs.railway.com/integrations/api",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://backboard.railway.com/graphql/v2",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}",
                },
                body={"query": "{ me { name email } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates the API token with a minimal viewer query",
            ),
        ),
    ],
)
