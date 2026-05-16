"""GitHub integration manifest.

Direct pydantic translation of the legacy
``modulex/py/app/integrations/tools/github_integration.json``. Per-action
``output_schema`` is intentionally NOT carried here; the modulex runtime
derives output JSONSchema from each ``@tool``'s return-type annotation
(see ``outputs.py``).
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
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
    name="github",
    display_name="GitHub",
    description="GitHub repository and code management platform",
    version="1.0.0",
    author="ModuleX",
    logo="logos:github-icon",
    app_url="https://github.com",
    categories=["Developer Tools & Infrastructure", "version-control", "productivity"],
    actions=[
        ActionDefinition(
            name="list_repositories",
            description="List repositories for the authenticated user or organization",
            parameters={
                "visibility": ParameterDef(
                    type="string",
                    description="Filter by visibility: all, public, private",
                    default="all",
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort by: created, updated, pushed, full_name",
                    default="full_name",
                ),
                "per_page": ParameterDef(
                    type="integer",
                    description="Results per page (max 100)",
                    default=30,
                ),
            },
        ),
        ActionDefinition(
            name="create_repository",
            description="Create a new repository",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="Repository name",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Repository description",
                ),
                "private": ParameterDef(
                    type="boolean",
                    description="Whether the repository is private",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_repository",
            description="Delete a repository (irreversible, requires delete_repo scope)",
            parameters={
                "owner": ParameterDef(
                    type="string",
                    description="Repository owner (username or organization)",
                    required=True,
                ),
                "repo": ParameterDef(
                    type="string",
                    description="Repository name to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_repository",
            description="Get repository details",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
            },
        ),
        ActionDefinition(
            name="list_issues",
            description="List issues for a repository",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "state": ParameterDef(
                    type="string",
                    description="Issue state: open, closed, all",
                    default="open",
                ),
            },
        ),
        ActionDefinition(
            name="create_issue",
            description="Create a new issue",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "title": ParameterDef(
                    type="string", description="Issue title", required=True
                ),
                "body": ParameterDef(type="string", description="Issue body"),
                "labels": ParameterDef(type="array", description="Issue labels"),
            },
        ),
        ActionDefinition(
            name="get_issue",
            description="Get issue details",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "issue_number": ParameterDef(
                    type="integer", description="Issue number", required=True
                ),
            },
        ),
        ActionDefinition(
            name="update_issue",
            description="Update an existing issue",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "issue_number": ParameterDef(
                    type="integer", description="Issue number", required=True
                ),
                "title": ParameterDef(type="string", description="Issue title"),
                "body": ParameterDef(type="string", description="Issue body"),
                "state": ParameterDef(
                    type="string", description="Issue state: open or closed"
                ),
            },
        ),
        ActionDefinition(
            name="list_pull_requests",
            description="List pull requests for a repository",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "state": ParameterDef(
                    type="string",
                    description="PR state: open, closed, all",
                    default="open",
                ),
            },
        ),
        ActionDefinition(
            name="create_pull_request",
            description="Create a new pull request",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "title": ParameterDef(
                    type="string", description="Pull request title", required=True
                ),
                "head": ParameterDef(
                    type="string",
                    description="The name of the branch where your changes are implemented",
                    required=True,
                ),
                "base": ParameterDef(
                    type="string",
                    description="The name of the branch you want the changes pulled into",
                    required=True,
                ),
                "body": ParameterDef(type="string", description="Pull request description"),
            },
        ),
        ActionDefinition(
            name="get_pull_request",
            description="Get pull request details",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "pull_number": ParameterDef(
                    type="integer", description="Pull request number", required=True
                ),
            },
        ),
        ActionDefinition(
            name="merge_pull_request",
            description="Merge a pull request",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "pull_number": ParameterDef(
                    type="integer", description="Pull request number", required=True
                ),
                "commit_message": ParameterDef(
                    type="string", description="Commit message for the merge"
                ),
                "merge_method": ParameterDef(
                    type="string",
                    description="Merge method: merge, squash, rebase",
                    default="merge",
                ),
            },
        ),
        ActionDefinition(
            name="create_branch",
            description="Create a new branch",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "branch_name": ParameterDef(
                    type="string", description="New branch name", required=True
                ),
                "from_branch": ParameterDef(
                    type="string",
                    description="Source branch (defaults to default branch)",
                ),
            },
        ),
        ActionDefinition(
            name="get_file_content",
            description="Get file contents from a repository",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "path": ParameterDef(
                    type="string", description="File path", required=True
                ),
                "branch": ParameterDef(
                    type="string",
                    description="Branch name (defaults to default branch)",
                ),
            },
        ),
        ActionDefinition(
            name="create_commit",
            description="Create a commit with file changes",
            parameters={
                "owner": ParameterDef(
                    type="string", description="Repository owner", required=True
                ),
                "repo": ParameterDef(
                    type="string", description="Repository name", required=True
                ),
                "branch": ParameterDef(
                    type="string", description="Branch name", required=True
                ),
                "message": ParameterDef(
                    type="string", description="Commit message", required=True
                ),
                "files": ParameterDef(
                    type="array",
                    description="Array of file objects with path and content",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="search_code",
            description="Search for code in repositories",
            parameters={
                "query": ParameterDef(
                    type="string", description="Search query", required=True
                ),
                "sort": ParameterDef(
                    type="string",
                    description="Sort by: indexed (default)",
                    default="indexed",
                ),
                "per_page": ParameterDef(
                    type="integer",
                    description="Results per page (max 100)",
                    default=30,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using GitHub OAuth (recommended for most use cases)",
            setup_environment_variables=[
                EnvVar(
                    name="GITHUB_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="GitHub OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="Iv1.xxxxxxxxxxxxxxxx",
                    about_url="https://github.com/settings/applications/new",
                ),
                EnvVar(
                    name="GITHUB_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="GitHub OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://github.com/settings/applications/new",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://github.com/login/oauth/authorize",
                token_url="https://github.com/login/oauth/access_token",
                scopes=["repo", "user", "read:org", "workflow"],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://api.github.com/user",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["login", "id"],
                ),
                cost_level="free",
                description=(
                    "Validates OAuth token by fetching authenticated user info "
                    "(no API cost)"
                ),
            ),
        ),
        BearerTokenAuthSchema(
            display_name="Personal Access Token",
            description="Use your GitHub Personal Access Token (Classic or Fine-grained)",
            setup_instructions=[
                "Go to GitHub Settings → Developer settings → Personal access tokens",
                "Choose 'Tokens (classic)' OR 'Fine-grained tokens (Beta)'",
                "Click 'Generate new token'",
                "For Classic: Select scopes (repo, user, read:org, workflow)",
                "For Fine-grained: Set repository access and permissions",
                "Copy the generated token",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GITHUB_PERSONAL_TOKEN",
                    display_name="Personal Access Token",
                    description=(
                        "Your GitHub Personal Access Token "
                        "(Classic: ghp_xxx or Fine-grained: github_pat_xxx)"
                    ),
                    required=True,
                    sensitive=True,
                    sample_format="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://github.com/settings/tokens",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.github.com/user",
                method="GET",
                headers={
                    "Authorization": "Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["login", "id"],
                ),
                cost_level="free",
                description=(
                    "Validates Personal Access Token by fetching authenticated user info "
                    "(no API cost)"
                ),
            ),
        ),
    ],
)
