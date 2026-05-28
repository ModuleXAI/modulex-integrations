"""Product Hunt integration manifest."""
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
    name="product_hunt",
    display_name="Product Hunt",
    description=(
        "Discover and explore tech products, topics, and community posts"
        " via the Product Hunt GraphQL API"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:product_hunt-themed",
    app_url="https://www.producthunt.com",
    categories=["Productivity & Collaboration", "Marketing"],
    actions=[
        ActionDefinition(
            name="list_topic_options",
            description="Retrieves available topic options with slug and display name",
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Product Hunt OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="PRODUCT_HUNT_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Product Hunt OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.producthunt.com/v2/oauth/applications",
                ),
                EnvVar(
                    name="PRODUCT_HUNT_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Product Hunt OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://www.producthunt.com/v2/oauth/applications",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://api.producthunt.com/v2/oauth/authorize",
                token_url="https://api.producthunt.com/v2/oauth/token",
                scopes=["public", "private"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.producthunt.com/v2/api/graphql",
                method="POST",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                body={"query": "{ viewer { id } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching the authenticated user via GraphQL",
            ),
        ),
    ],
)
