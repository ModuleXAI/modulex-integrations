"""Linear integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="linear",
    display_name="Linear",
    description=(
        "Modern project management and issue tracking tool for software "
        "teams. Streamline workflows, track bugs, and coordinate tasks "
        "with powerful search, filtering, and automation capabilities."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:linear-themed",
    app_url="https://linear.app",
    categories=["Project & Task Management", "task_management", "collaboration"],
    actions=[
        ActionDefinition(
            name="get_teams",
            description=(
                "Retrieve all teams in your Linear workspace. Use this to "
                "discover available teams before creating issues or projects."
            ),
            parameters={
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of teams to return",
                    default=50,
                ),
                "after": ParameterDef(
                    type="string", description="Cursor for pagination"
                ),
            },
        ),
        ActionDefinition(
            name="get_issue",
            description=(
                "Retrieve a Linear issue by its ID. Returns title, "
                "description, state, assignee, team, project, labels, and "
                "timestamps."
            ),
            parameters={
                "issue_id": ParameterDef(
                    type="string",
                    description="The ID of the issue to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_issues",
            description=(
                "Search Linear issues by team, project, assignee, labels, "
                "state, or text query."
            ),
            parameters={
                "team_id": ParameterDef(type="string", description="Filter by team ID"),
                "project_id": ParameterDef(
                    type="string", description="Filter by project ID"
                ),
                "assignee_id": ParameterDef(
                    type="string", description="Filter by assignee user ID"
                ),
                "state_id": ParameterDef(
                    type="string", description="Filter by workflow state ID"
                ),
                "query": ParameterDef(
                    type="string", description="Substring to match in issue titles"
                ),
                "label_names": ParameterDef(
                    type="array", description="Filter by label names"
                ),
                "include_archived": ParameterDef(
                    type="boolean",
                    description="Include archived issues",
                    default=False,
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Field to order by ('createdAt' or 'updatedAt')",
                    default="updatedAt",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of issues to return",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="create_issue",
            description="Create a new issue in Linear.",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description=(
                        "The team's UUID (the 'id' field returned by "
                        "get_teams) — NOT the short team key like 'ENG'. "
                        "Call get_teams first to resolve it."
                    ),
                    required=True,
                ),
                "title": ParameterDef(
                    type="string", description="The title of the issue", required=True
                ),
                "description": ParameterDef(
                    type="string", description="Markdown description"
                ),
                "assignee_id": ParameterDef(
                    type="string",
                    description="UUID of the user to assign the issue to",
                ),
                "project_id": ParameterDef(
                    type="string", description="UUID of the project to add the issue to"
                ),
                "state_id": ParameterDef(
                    type="string", description="UUID of the workflow state"
                ),
                "label_ids": ParameterDef(
                    type="array", description="Label UUIDs to attach"
                ),
                "priority": ParameterDef(
                    type="integer",
                    description=(
                        "Priority level: 0=No priority, 1=Urgent, 2=High, "
                        "3=Normal, 4=Low"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="update_issue",
            description="Update an existing Linear issue.",
            parameters={
                "issue_id": ParameterDef(
                    type="string",
                    description="The ID of the issue to update",
                    required=True,
                ),
                "title": ParameterDef(type="string", description="New title"),
                "description": ParameterDef(
                    type="string", description="New markdown description"
                ),
                "assignee_id": ParameterDef(
                    type="string", description="New assignee user ID"
                ),
                "team_id": ParameterDef(
                    type="string", description="Move to a different team"
                ),
                "project_id": ParameterDef(
                    type="string", description="Move to a different project"
                ),
                "state_id": ParameterDef(
                    type="string", description="Change workflow state"
                ),
                "label_ids": ParameterDef(
                    type="array", description="Replace labels with these IDs"
                ),
                "priority": ParameterDef(
                    type="integer", description="New priority level (0-4)"
                ),
            },
        ),
        ActionDefinition(
            name="list_projects",
            description=(
                "List projects in Linear with optional team filtering and "
                "pagination."
            ),
            parameters={
                "team_id": ParameterDef(type="string", description="Filter by team ID"),
                "order_by": ParameterDef(
                    type="string",
                    description="Field to order by ('createdAt' or 'updatedAt')",
                    default="updatedAt",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of projects to return",
                    default=50,
                ),
                "after": ParameterDef(
                    type="string", description="Cursor for pagination"
                ),
            },
        ),
        ActionDefinition(
            name="create_project",
            description="Create a new project in Linear.",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description=(
                        "The team's UUID (the 'id' field returned by "
                        "get_teams) — NOT the short team key like 'ENG'. "
                        "Call get_teams first to resolve it."
                    ),
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="The name of the project",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string", description="The description of the project"
                ),
                "status_id": ParameterDef(
                    type="string", description="The project-status ID"
                ),
                "priority": ParameterDef(
                    type="integer", description="Priority level (0-4)"
                ),
                "member_ids": ParameterDef(
                    type="array", description="IDs of users to add as members"
                ),
                "start_date": ParameterDef(
                    type="string", description="Start date (YYYY-MM-DD)"
                ),
                "target_date": ParameterDef(
                    type="string", description="Target date (YYYY-MM-DD)"
                ),
                "label_ids": ParameterDef(
                    type="array", description="Label IDs to attach"
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Linear OAuth (recommended for most use cases)",
            setup_environment_variables=[
                EnvVar(
                    name="LINEAR_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Linear OAuth application Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://linear.app/settings/api/applications/new",
                ),
                EnvVar(
                    name="LINEAR_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Linear OAuth application Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 64,
                    about_url="https://linear.app/settings/api/applications/new",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://linear.app/oauth/authorize",
                token_url="https://api.linear.app/oauth/token",
                scopes=["read", "write"],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://api.linear.app/graphql",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {access_token}",
                },
                body={"query": "query { viewer { id name } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["data.viewer.id"]
                ),
                cost_level="minimal",
                description="Validates the OAuth token with a trivial viewer query",
            ),
        ),
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your Linear API key. Generate one from "
                "Linear Settings > API > Personal API keys."
            ),
            setup_environment_variables=[
                EnvVar(
                    name="LINEAR_API_KEY",
                    display_name="Linear API Key",
                    description="Your Linear personal API key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="lin_api_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://linear.app/settings/api",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.linear.app/graphql",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "{api_key}",
                },
                body={"query": "query { viewer { id name } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200], response_fields=["data.viewer.id"]
                ),
                cost_level="minimal",
                description="Validates API key with a trivial viewer query",
            ),
        ),
    ],
)
