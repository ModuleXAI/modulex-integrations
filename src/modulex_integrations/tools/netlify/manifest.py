"""Netlify integration manifest."""
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
    name="netlify",
    display_name="Netlify",
    description="Web hosting and automation platform for modern web projects",
    version="1.0.0",
    author="ModuleX",
    logo="logos:netlify-icon",
    app_url="https://www.netlify.com",
    categories=["Developer Tools & Infrastructure", "hosting", "ci-cd"],
    actions=[
        ActionDefinition(
            name="get_site",
            description="Get a specified site by its ID",
            parameters={
                "site_id": ParameterDef(
                    type="string",
                    description="The Netlify site ID to retrieve information for",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_files",
            description="Returns a list of all the files in the current deploy for a site",
            parameters={
                "site_id": ParameterDef(
                    type="string",
                    description="The Netlify site ID to list files for",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_site_deploys",
            description="Returns a list of all deploys for a specific site",
            parameters={
                "site_id": ParameterDef(
                    type="string",
                    description="The Netlify site ID to list deploys for",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of deploys to return",
                    default=None,
                ),
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to fetch (1-500)",
                    default=50,
                ),
            },
        ),
        ActionDefinition(
            name="rollback_deploy",
            description="Restores an old deploy and makes it the live version of the site",
            parameters={
                "site_id": ParameterDef(
                    type="string",
                    description="The Netlify site ID to rollback a deploy for",
                    required=True,
                ),
                "deploy_id": ParameterDef(
                    type="string",
                    description="The deploy ID to restore",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Netlify OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="NETLIFY_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Netlify OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://app.netlify.com/user/applications",
                ),
                EnvVar(
                    name="NETLIFY_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Netlify OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://app.netlify.com/user/applications",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://app.netlify.com/authorize",
                token_url="https://api.netlify.com/oauth/token",
                scopes=[],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.netlify.com/api/v1/user",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user info",
            ),
        ),
    ],
)
