"""TinyURL integration manifest."""
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


manifest = IntegrationManifest(
    name="tinyurl",
    display_name="TinyURL",
    description=(
        "Professional URL shortening service with custom aliases, "
        "analytics, and link management features"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:tinyurl-themed",
    app_url="https://tinyurl.com",
    categories=["Marketing & Advertising", "Utilities", "link", "miscellaneous"],
    actions=[
        ActionDefinition(
            name="create_shortened_link",
            description=(
                "Create a new shortened URL with optional custom alias, tags, "
                "and expiration settings"
            ),
            parameters={
                "url": ParameterDef(
                    type="string",
                    description="The long URL that will be shortened",
                    required=True,
                ),
                "domain": ParameterDef(
                    type="string",
                    description=(
                        "Domain for the TinyURL (default: tinyurl.com, or use "
                        "branded domains with subscription)"
                    ),
                    default="tinyurl.com",
                ),
                "alias": ParameterDef(
                    type="string",
                    description="Custom alias (auto-generated if not provided)",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Tags to group and categorize TinyURLs (paid only)",
                ),
                "expires_at": ParameterDef(
                    type="string",
                    description="Expiration ISO8601 datetime. Paid only",
                ),
                "description": ParameterDef(
                    type="string", description="Description for the alias"
                ),
            },
        ),
        ActionDefinition(
            name="retrieve_link_analytics",
            description=(
                "Get analytics for a TinyURL including total clicks, geographic "
                "breakdowns, and device types. Requires paid account"
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain of the TinyURL",
                    default="tinyurl.com",
                ),
                "alias": ParameterDef(
                    type="string",
                    description="Alias of the TinyURL to get analytics for",
                    required=True,
                ),
                "from_date": ParameterDef(
                    type="string",
                    description="Start datetime for analytics report (ISO8601)",
                    required=True,
                ),
                "to_date": ParameterDef(
                    type="string", description="End datetime; defaults to now"
                ),
                "tag": ParameterDef(
                    type="string", description="Tag to filter analytics by"
                ),
            },
        ),
        ActionDefinition(
            name="update_link_metadata",
            description=(
                "Update the metadata of an existing TinyURL including domain, "
                "alias, analytics settings, and expiration"
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Current domain of the TinyURL",
                    required=True,
                ),
                "alias": ParameterDef(
                    type="string",
                    description="Current alias of the TinyURL",
                    required=True,
                ),
                "new_domain": ParameterDef(
                    type="string", description="New domain to switch to"
                ),
                "new_alias": ParameterDef(
                    type="string", description="New alias to switch to"
                ),
                "new_stats": ParameterDef(
                    type="boolean",
                    description="Enable or disable click analytics collection",
                ),
                "new_tags": ParameterDef(
                    type="array",
                    description="New tags (overwrites existing). Paid only",
                ),
                "new_expires_at": ParameterDef(
                    type="string",
                    description="New expiration ISO8601 datetime. Paid only",
                ),
                "new_description": ParameterDef(
                    type="string", description="New description for the alias"
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Token Authentication",
            description="Authenticate using your TinyURL API token",
            setup_instructions=[
                "Log in to your TinyURL account at https://tinyurl.com",
                "Navigate to Settings or API section",
                "Generate or copy your API token",
                "Use the token to authenticate API requests",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="TINYURL_API_KEY",
                    display_name="TinyURL API Token",
                    description="Your TinyURL API token for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="x" * 32,
                    about_url="https://tinyurl.com/app/dev",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.tinyurl.com/create",
                method="POST",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                body={"url": "https://example.com/test"},
                success_indicators=SuccessIndicators(status_codes=[200, 201]),
                cost_level="low",
                description="Validates API token by creating a test TinyURL",
            ),
        ),
    ],
)
