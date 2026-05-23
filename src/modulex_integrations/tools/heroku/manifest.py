"""Heroku integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="heroku",
    display_name="Heroku",
    description="Cloud platform for building, deploying, and managing applications",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:heroku-themed",
    app_url="https://www.heroku.com",
    categories=["Developer Tools & Infrastructure", "cloud-infrastructure", "paas"],
    actions=[
        ActionDefinition(
            name="list_apps",
            description="List all apps accessible by the authenticated user",
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Heroku OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="HEROKU_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Heroku OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://dashboard.heroku.com/account/applications",
                ),
                EnvVar(
                    name="HEROKU_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Heroku OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://dashboard.heroku.com/account/applications",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://id.heroku.com/oauth/authorize",
                token_url="https://id.heroku.com/oauth/token",
                scopes=["global"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.heroku.com/account",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Accept": "application/vnd.heroku+json; version=3",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated account",
            ),
        ),
    ],
)
