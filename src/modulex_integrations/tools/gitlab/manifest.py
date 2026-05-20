"""GitLab integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
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
    name="gitlab",
    display_name="GitLab",
    description="GitLab repository and project management platform",
    version="1.0.0",
    author="ModuleX",
    logo="logos:gitlab-icon",
    app_url="https://gitlab.com",
    categories=["Developer Tools & Infrastructure", "version-control", "project-management"],
    actions=[
        ActionDefinition(
            name="create_branch",
            description="Create a new branch in a GitLab repository",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "ref": ParameterDef(
                    type="string",
                    description="The branch name or commit SHA to create the new branch from",
                    required=True,
                ),
                "branch_name": ParameterDef(
                    type="string",
                    description="The name of the branch to create",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_epic",
            description="Create a new epic in a GitLab group (requires GitLab Premium or Ultimate)",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="The ID of the group",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the epic",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="The description of the epic",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names for the epic",
                ),
                "parent_id": ParameterDef(
                    type="string",
                    description="The internal ID of the parent epic (requires GitLab Premium or Ultimate)",
                ),
                "color": ParameterDef(
                    type="string",
                    description="The color of the epic (introduced in GitLab 14.8)",
                ),
                "confidential": ParameterDef(
                    type="boolean",
                    description="Whether the epic should be confidential",
                ),
                "created_at": ParameterDef(
                    type="string",
                    description="When the epic was created, ISO 8601 format (requires admin or owner privileges)",
                ),
                "start_date_is_fixed": ParameterDef(
                    type="boolean",
                    description="Whether start date should be sourced from start_date_fixed or from milestones",
                ),
                "due_date_is_fixed": ParameterDef(
                    type="boolean",
                    description="Whether due date should be sourced from due_date_fixed or from milestones",
                ),
                "start_date_fixed": ParameterDef(
                    type="string",
                    description="The fixed start date of the epic, ISO 8601 format (relevant when start_date_is_fixed is true)",
                ),
                "due_date_fixed": ParameterDef(
                    type="string",
                    description="The fixed due date of the epic, ISO 8601 format (relevant when due_date_is_fixed is true)",
                ),
            },
        ),
        ActionDefinition(
            name="create_issue",
            description="Create a new issue in a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the issue",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="The description of the issue",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names for the issue",
                ),
                "assignee_ids": ParameterDef(
                    type="array",
                    description="List of user IDs to assign the issue to",
                ),
            },
        ),
        ActionDefinition(
            name="get_issue",
            description="Get a single issue from a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "issue_iid": ParameterDef(
                    type="string",
                    description="The internal ID of the project issue",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_repo_branch",
            description="Get a single repository branch from a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "branch": ParameterDef(
                    type="string",
                    description="The name of the branch",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_commits",
            description="List commits in a GitLab repository branch",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "ref_name": ParameterDef(
                    type="string",
                    description="The name of a repository branch, tag, or revision range; defaults to the default branch if not given",
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of commits to return (per_page)",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_groups",
            description="List all groups accessible to the authenticated user",
            parameters={
                "min_access_level": ParameterDef(
                    type="integer",
                    description="Limit to groups where the user has at least this access level: 10 (Guest), 20 (Reporter), 30 (Developer), 40 (Maintainer), 50 (Owner)",
                ),
                "top_level_only": ParameterDef(
                    type="boolean",
                    description="Limit to top-level groups, excluding all subgroups",
                ),
                "search": ParameterDef(
                    type="string",
                    description="Return groups matching this search string",
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Order groups by: name, path, id, or similarity (must be similarity when search is provided)",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort order: asc or desc",
                    default="asc",
                ),
                "active": ParameterDef(
                    type="boolean",
                    description="Limit to groups that are not archived and not marked for deletion",
                ),
                "archived": ParameterDef(
                    type="boolean",
                    description="Limit to groups that are archived",
                ),
            },
        ),
        ActionDefinition(
            name="list_project_members",
            description="List all members of a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="Filter results by name, email, or username (partial values accepted)",
                ),
                "user_ids": ParameterDef(
                    type="array",
                    description="List of user IDs to filter results to",
                ),
                "skip_users": ParameterDef(
                    type="array",
                    description="List of user IDs to exclude from results",
                ),
                "show_seat_info": ParameterDef(
                    type="boolean",
                    description="Return seat information for each member if available",
                ),
            },
        ),
        ActionDefinition(
            name="list_repo_branches",
            description="Get a list of repository branches from a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "search": ParameterDef(
                    type="string",
                    description="Return branches containing this search string (use ^term and term$ for prefix/suffix matching)",
                ),
            },
        ),
        ActionDefinition(
            name="search_issues",
            description="Search for issues in a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "search": ParameterDef(
                    type="string",
                    description="Search issues against their title and description",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names; issues must have all labels to be returned",
                ),
                "state": ParameterDef(
                    type="string",
                    description="Return issues by state: all, opened, or closed",
                    default="all",
                ),
                "assignee_id": ParameterDef(
                    type="string",
                    description="Return issues assigned to the given user ID",
                ),
                "max": ParameterDef(
                    type="integer",
                    description="Maximum number of issues to return (per_page)",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="update_epic",
            description="Update an existing epic in a GitLab group (requires GitLab Premium or Ultimate)",
            parameters={
                "group_id": ParameterDef(
                    type="string",
                    description="The ID of the group",
                    required=True,
                ),
                "epic_iid": ParameterDef(
                    type="string",
                    description="The internal ID of the epic",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the epic",
                ),
                "description": ParameterDef(
                    type="string",
                    description="The description of the epic",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names for the epic (set empty to unassign all)",
                ),
                "add_labels": ParameterDef(
                    type="array",
                    description="Labels to add to the epic",
                ),
                "remove_labels": ParameterDef(
                    type="array",
                    description="Labels to remove from the epic",
                ),
                "parent_id": ParameterDef(
                    type="string",
                    description="The ID of a parent epic (available in GitLab 14.6+)",
                ),
                "state_event": ParameterDef(
                    type="string",
                    description="State event for the epic: close or reopen",
                ),
                "confidential": ParameterDef(
                    type="boolean",
                    description="Whether the epic should be confidential",
                ),
                "color": ParameterDef(
                    type="string",
                    description="The color of the epic",
                ),
                "updated_at": ParameterDef(
                    type="string",
                    description="When the epic was updated, ISO 8601 format (requires admin or owner privileges)",
                ),
                "start_date_is_fixed": ParameterDef(
                    type="boolean",
                    description="Whether start date should be sourced from start_date_fixed or from milestones",
                ),
                "due_date_is_fixed": ParameterDef(
                    type="boolean",
                    description="Whether due date should be sourced from due_date_fixed or from milestones",
                ),
                "start_date_fixed": ParameterDef(
                    type="string",
                    description="The fixed start date of the epic, ISO 8601 format (relevant when start_date_is_fixed is true)",
                ),
                "due_date_fixed": ParameterDef(
                    type="string",
                    description="The fixed due date of the epic, ISO 8601 format (relevant when due_date_is_fixed is true)",
                ),
            },
        ),
        ActionDefinition(
            name="update_issue",
            description="Update an existing issue in a GitLab project",
            parameters={
                "project_id": ParameterDef(
                    type="integer",
                    description="The project ID, as displayed in the main project page",
                    required=True,
                ),
                "issue_iid": ParameterDef(
                    type="string",
                    description="The internal ID of the issue",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the issue",
                ),
                "description": ParameterDef(
                    type="string",
                    description="The description of the issue",
                ),
                "labels": ParameterDef(
                    type="array",
                    description="List of label names for the issue (set empty to unassign all)",
                ),
                "assignee_ids": ParameterDef(
                    type="array",
                    description="List of user IDs to assign the issue to (set to 0 or empty to unassign all)",
                ),
                "state_event": ParameterDef(
                    type="string",
                    description="State event for the issue: close or reopen",
                ),
                "discussion_locked": ParameterDef(
                    type="boolean",
                    description="Whether the issue discussion is locked (only project members can add or edit comments when locked)",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using GitLab OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GITLAB_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="GitLab OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://gitlab.com/-/user_settings/applications",
                ),
                EnvVar(
                    name="GITLAB_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="GitLab OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://gitlab.com/-/user_settings/applications",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://gitlab.com/oauth/authorize",
                token_url="https://gitlab.com/oauth/token",
                scopes=["api"],
            ),
            test_endpoint=TestEndpoint(
                url="https://gitlab.com/api/v4/user",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user",
            ),
        ),
    ],
)
