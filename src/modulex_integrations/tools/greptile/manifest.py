"""Greptile integration manifest.

Greptile uses an API-key credential: a Greptile API key (sent as a Bearer
token) plus a GitHub Personal Access Token (sent as the ``X-GitHub-Token``
header so Greptile can clone the target repositories). The runtime injects
``api_key`` directly and persists the GitHub token into ``auth_data`` so each
tool receives it as the ``github_token`` parameter.
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


_REPOSITORIES_DESCRIPTION = (
    "Comma-separated list of repositories. Format: 'github:branch:owner/repo' "
    "or just 'owner/repo' (defaults to github:main). "
    "Example: 'facebook/react' or 'github:main:facebook/react,github:main:facebook/relay'"
)


manifest = IntegrationManifest(
    name="greptile",
    display_name="Greptile",
    description=(
        "Query and search codebases using natural language with Greptile. Get "
        "AI-generated answers about your code, find relevant files, and "
        "understand complex codebases."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:greptile",
    app_url="https://www.greptile.com",
    categories=["Developer Tools & Infrastructure", "version-control", "knowledge-base"],
    actions=[
        ActionDefinition(
            name="query",
            description=(
                "Query repositories in natural language and get answers with relevant "
                "code references. Greptile uses AI to understand your codebase and "
                "answer questions."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Natural language question about the codebase",
                    required=True,
                ),
                "repositories": ParameterDef(
                    type="string",
                    description=_REPOSITORIES_DESCRIPTION,
                    required=True,
                ),
                "session_id": ParameterDef(
                    type="string",
                    description=(
                        "Optional session ID for conversation continuity across "
                        "multiple queries"
                    ),
                ),
                "genius": ParameterDef(
                    type="boolean",
                    description=(
                        "Enable genius mode for more thorough analysis "
                        "(slower but more accurate)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="search",
            description=(
                "Search repositories in natural language and get relevant code "
                "references without generating an answer. Useful for finding specific "
                "code locations."
            ),
            parameters={
                "query": ParameterDef(
                    type="string",
                    description="Natural language search query to find relevant code",
                    required=True,
                ),
                "repositories": ParameterDef(
                    type="string",
                    description=_REPOSITORIES_DESCRIPTION,
                    required=True,
                ),
                "session_id": ParameterDef(
                    type="string",
                    description=(
                        "Optional session ID for conversation continuity across "
                        "multiple searches"
                    ),
                ),
                "genius": ParameterDef(
                    type="boolean",
                    description=(
                        "Enable genius mode for more thorough search "
                        "(slower but more accurate)"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="index_repo",
            description=(
                "Submit a repository to be indexed by Greptile. Indexing must complete "
                "before the repository can be queried. Small repos take 3-5 minutes, "
                "larger ones can take over an hour."
            ),
            parameters={
                "remote": ParameterDef(
                    type="string",
                    description="Git remote type: 'github' or 'gitlab'",
                    default="github",
                    required=True,
                ),
                "repository": ParameterDef(
                    type="string",
                    description="Repository in owner/repo format. Example: 'facebook/react'",
                    required=True,
                ),
                "branch": ParameterDef(
                    type="string",
                    description="Branch to index (e.g. 'main' or 'master')",
                    required=True,
                ),
                "reload": ParameterDef(
                    type="boolean",
                    description="Force re-indexing even if already indexed",
                ),
                "notify": ParameterDef(
                    type="boolean",
                    description="Send email notification when indexing completes",
                ),
            },
        ),
        ActionDefinition(
            name="status",
            description=(
                "Check the indexing status of a repository. Use this to verify if a "
                "repository is ready to be queried or to monitor indexing progress."
            ),
            parameters={
                "remote": ParameterDef(
                    type="string",
                    description="Git remote type: 'github' or 'gitlab'",
                    default="github",
                    required=True,
                ),
                "repository": ParameterDef(
                    type="string",
                    description="Repository in owner/repo format. Example: 'facebook/react'",
                    required=True,
                ),
                "branch": ParameterDef(
                    type="string",
                    description="Branch name (e.g. 'main' or 'master')",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description=(
                "Authenticate using your Greptile API key plus a GitHub Personal "
                "Access Token so Greptile can access your repositories"
            ),
            setup_instructions=[
                "Go to https://app.greptile.com and sign up or log in",
                "Open Settings and create a new API key",
                "Paste the Greptile API key below",
                (
                    "Create a GitHub Personal Access Token with 'repo' read access at "
                    "https://github.com/settings/tokens and paste it as the GitHub token"
                ),
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GREPTILE_API_KEY",
                    display_name="Greptile API Key",
                    description="Your Greptile API key from app.greptile.com",
                    required=True,
                    sensitive=True,
                    about_url="https://app.greptile.com",
                ),
                EnvVar(
                    name="GREPTILE_GITHUB_TOKEN",
                    display_name="GitHub Token",
                    description=(
                        "A GitHub Personal Access Token with 'repo' read access, used "
                        "by Greptile to clone and index your repositories"
                    ),
                    required=True,
                    sensitive=True,
                    inject_into_auth_data=True,
                    about_url="https://github.com/settings/tokens",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.greptile.com/v2/repositories/github%3Amain%3Agreptileai%2Fgreptile",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "X-GitHub-Token": "{github_token}",
                },
                success_indicators=SuccessIndicators(status_codes=[200, 404]),
                cost_level="free",
                description=(
                    "Validates the Greptile API key by requesting a repository status "
                    "(200 when indexed, 404 when not — both confirm the key is accepted)"
                ),
            ),
        ),
    ],
)
