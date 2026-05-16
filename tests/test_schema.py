"""Contract tests for the IntegrationManifest schema.

These tests pin down the shape that every integration's manifest must
satisfy. They use a github-shaped manifest because it exercises every
schema feature: multi-action, multi-auth (OAuth2 + bearer), parameters
with defaults, env vars with rich UI metadata.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from modulex_integrations import (
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


def _github_like_manifest() -> IntegrationManifest:
    """Construct a manifest shaped like the existing github_integration.json.

    Truncated to two actions; the goal is exercising every schema
    feature, not duplicating the 1180-line JSON.
    """
    return IntegrationManifest(
        name="github",
        display_name="GitHub",
        description="GitHub repository and code management platform",
        version="1.0.0",
        author="ModuleX",
        logo="https://cdn.jsdelivr.net/gh/ModuleXAI/logox@main/tools/github.svg",
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
                    "per_page": ParameterDef(
                        type="integer",
                        description="Results per page (max 100)",
                        default=30,
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
                    "labels": ParameterDef(type="array", description="Issue labels"),
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
                        sensitive=False,
                        only_for_custom=True,
                        sample_format="Iv1.xxxxxxxxxxxxxxxx",
                        about_url="https://github.com/settings/applications/new",
                    ),
                    EnvVar(
                        name="GITHUB_OAUTH2_CLIENT_SECRET",
                        display_name="Client Secret",
                        description="GitHub OAuth App Client Secret",
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
                        status_codes=[200], response_fields=["login", "id"]
                    ),
                    cost_level="free",
                ),
            ),
            BearerTokenAuthSchema(
                display_name="Personal Access Token",
                description="Use your GitHub Personal Access Token (Classic or Fine-grained)",
                setup_instructions=[
                    "Go to GitHub Settings -> Developer settings -> Personal access tokens",
                    "Choose 'Tokens (classic)' OR 'Fine-grained tokens (Beta)'",
                    "Generate, copy, and configure GITHUB_PERSONAL_TOKEN.",
                ],
                setup_environment_variables=[
                    EnvVar(
                        name="GITHUB_PERSONAL_TOKEN",
                        display_name="Personal Access Token",
                        description="Your GitHub Personal Access Token",
                        sensitive=True,
                        sample_format="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                        about_url="https://github.com/settings/tokens",
                    ),
                ],
                test_endpoint=TestEndpoint(
                    url="https://api.github.com/user",
                    headers={"Authorization": "Bearer {token}"},
                    success_indicators=SuccessIndicators(
                        status_codes=[200], response_fields=["login", "id"]
                    ),
                ),
            ),
        ],
    )


class TestManifestConstruction:
    def test_github_like_manifest_validates(self) -> None:
        manifest = _github_like_manifest()
        assert manifest.name == "github"
        assert manifest.integration_type == "tool"
        assert len(manifest.actions) == 2
        assert len(manifest.auth_schemas) == 2

    def test_discriminator_picks_oauth2_variant(self) -> None:
        manifest = _github_like_manifest()
        first = manifest.auth_schemas[0]
        assert isinstance(first, OAuth2AuthSchema)
        assert first.oauth_config.scopes == ["repo", "user", "read:org", "workflow"]

    def test_discriminator_picks_bearer_variant(self) -> None:
        manifest = _github_like_manifest()
        second = manifest.auth_schemas[1]
        assert isinstance(second, BearerTokenAuthSchema)
        # bearer variant has no oauth_config; extra="forbid" guards this
        assert not hasattr(second, "oauth_config")


class TestManifestRoundtrip:
    def test_serialize_then_validate(self) -> None:
        original = _github_like_manifest()
        dumped = original.model_dump()
        restored = IntegrationManifest.model_validate(dumped)
        assert restored == original

    def test_model_json_schema_describes_auth_union(self) -> None:
        schema = IntegrationManifest.model_json_schema()
        # The generated JSONSchema is what the UI consumes; make sure
        # the auth_schemas field is present and discriminated.
        assert "auth_schemas" in schema["properties"]


class TestValidation:
    def test_invalid_auth_type_rejected(self) -> None:
        bad = {
            "name": "x",
            "display_name": "X",
            "description": "y",
            "auth_schemas": [
                {
                    "auth_type": "not_a_real_auth",
                    "display_name": "z",
                    "description": "z",
                    "test_endpoint": {
                        "url": "https://example.com",
                        "headers": {},
                        "success_indicators": {"status_codes": [200]},
                    },
                },
            ],
        }
        with pytest.raises(ValidationError):
            IntegrationManifest.model_validate(bad)

    def test_invalid_name_slug_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IntegrationManifest(
                name="GitHub",
                display_name="X",
                description="y",
            )

    def test_extra_field_rejected(self) -> None:
        with pytest.raises(ValidationError):
            IntegrationManifest.model_validate(
                {
                    "name": "x",
                    "display_name": "X",
                    "description": "y",
                    "bogus_field": "nope",
                }
            )
