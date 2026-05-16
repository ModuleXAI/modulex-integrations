"""Short.io integration manifest."""
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


def _utm_params() -> dict[str, ParameterDef]:
    return {
        "utm_source": ParameterDef(type="string", description="UTM source parameter"),
        "utm_medium": ParameterDef(type="string", description="UTM medium parameter"),
        "utm_campaign": ParameterDef(type="string", description="UTM campaign parameter"),
        "utm_term": ParameterDef(type="string", description="UTM term parameter"),
        "utm_content": ParameterDef(type="string", description="UTM content parameter"),
    }


manifest = IntegrationManifest(
    name="short_io",
    display_name="Short.io",
    description=(
        "URL shortening and link management platform with advanced "
        "analytics, custom domains, and device targeting."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="https://cdn.jsdelivr.net/gh/ModuleXAI/logox@main/tools/shortio.svg",
    app_url="https://short.io",
    categories=["Utilities", "link_management", "analytics"],
    actions=[
        ActionDefinition(
            name="create_link",
            description=(
                "Create a new short link with optional customization "
                "including custom paths, device-specific redirects, UTM "
                "parameters, and expiration"
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain name for the short link",
                    required=True,
                ),
                "original_url": ParameterDef(
                    type="string",
                    description="The original URL to shorten",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Custom path for the short link (auto-generated if empty)",
                ),
                "title": ParameterDef(
                    type="string", description="Title for the link shown in admin panel"
                ),
                "tags": ParameterDef(
                    type="array", description="Tags for organizing links"
                ),
                "allow_duplicates": ParameterDef(
                    type="boolean", description="Allow duplicate links for same URL"
                ),
                "expires_at": ParameterDef(
                    type="string", description="Expiration date in yyyy-mm-dd format"
                ),
                "expired_url": ParameterDef(
                    type="string", description="URL to redirect to when link expires"
                ),
                "iphone_url": ParameterDef(
                    type="string", description="Redirect URL for iPhone users"
                ),
                "android_url": ParameterDef(
                    type="string", description="Redirect URL for Android users"
                ),
                "password": ParameterDef(
                    type="string",
                    description="Password protection (Personal plan required)",
                ),
                **_utm_params(),
                "cloaking": ParameterDef(
                    type="boolean", description="Enable link cloaking"
                ),
                "redirect_type": ParameterDef(
                    type="integer",
                    description="HTTP redirect status code (301, 302, 303, 307, 308)",
                ),
                "folder_id": ParameterDef(
                    type="string", description="Folder ID to organize the link"
                ),
            },
        ),
        ActionDefinition(
            name="update_link",
            description=(
                "Update an existing short link's properties including "
                "original URL, path, title, and redirect settings"
            ),
            parameters={
                "link_id": ParameterDef(
                    type="string",
                    description="The ID of the link to update",
                    required=True,
                ),
                "original_url": ParameterDef(type="string", description="New original URL"),
                "path": ParameterDef(type="string", description="New custom path"),
                "title": ParameterDef(type="string", description="New title"),
                "tags": ParameterDef(type="array", description="New tags"),
                "expires_at": ParameterDef(
                    type="string",
                    description="New expiration date in yyyy-mm-dd format",
                ),
                "expired_url": ParameterDef(
                    type="string", description="New expired redirect URL"
                ),
                "iphone_url": ParameterDef(
                    type="string", description="New iPhone redirect URL"
                ),
                "android_url": ParameterDef(
                    type="string", description="New Android redirect URL"
                ),
                "password": ParameterDef(type="string", description="New password"),
                **_utm_params(),
                "cloaking": ParameterDef(
                    type="boolean", description="Enable/disable cloaking"
                ),
                "redirect_type": ParameterDef(
                    type="integer", description="New HTTP redirect status code"
                ),
            },
        ),
        ActionDefinition(
            name="delete_link",
            description="Permanently delete a short link. This action cannot be undone",
            parameters={
                "link_id": ParameterDef(
                    type="string",
                    description="The ID of the link to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="expire_link",
            description=(
                "Set expiration date for a short link and configure the "
                "redirect URL after expiration"
            ),
            parameters={
                "link_id": ParameterDef(
                    type="string",
                    description="The ID of the link to expire",
                    required=True,
                ),
                "expires_at": ParameterDef(
                    type="string",
                    description="Expiration date in yyyy-mm-dd format",
                    required=True,
                ),
                "expired_url": ParameterDef(
                    type="string",
                    description="URL to redirect to when link expires",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_link_info",
            description=(
                "Retrieve detailed information about a specific short link "
                "by domain and path"
            ),
            parameters={
                "domain": ParameterDef(
                    type="string",
                    description="Domain of the short link",
                    required=True,
                ),
                "path": ParameterDef(
                    type="string",
                    description="Path of the short link (without leading slash)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_links",
            description="List all short links associated with a specific domain",
            parameters={
                "domain_id": ParameterDef(
                    type="integer",
                    description="Domain ID to list links for",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of links to return (max 150)",
                    default=150,
                ),
            },
        ),
        ActionDefinition(
            name="list_domains",
            description="List all domains configured in your Short.io account",
            parameters={},
        ),
        ActionDefinition(
            name="get_domain_statistics",
            description=(
                "Retrieve detailed click statistics and analytics for a "
                "specific domain"
            ),
            parameters={
                "domain_id": ParameterDef(
                    type="integer",
                    description="Domain ID to get statistics for",
                    required=True,
                ),
                "period": ParameterDef(
                    type="string",
                    description=(
                        "Time period: total, custom, today, yesterday, "
                        "week, month, lastmonth, last7, last30"
                    ),
                    default="last30",
                ),
                "clicks_chart_interval": ParameterDef(
                    type="string",
                    description="Chart interval: hour, day, week, month",
                ),
                "tz_offset": ParameterDef(
                    type="integer", description="Timezone offset in minutes"
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Start date for custom period (yyyy-mm-dd)",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="End date for custom period (yyyy-mm-dd)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Short.io Secret API Key",
            setup_instructions=[
                "Log in to your Short.io account",
                "Go to Settings & Integrations",
                "Click on 'Integrations & API'",
                "Copy your Secret API Key",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SHORT_IO_API_KEY",
                    display_name="Short.io Secret API Key",
                    description="Your Short.io Secret API Key for authentication",
                    required=True,
                    sensitive=True,
                    sample_format="sk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://developers.short.io/reference/getting-started",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.short.io/api/domains",
                method="GET",
                headers={
                    "Authorization": "{api_key}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates API key by listing domains (no API cost)",
            ),
        ),
    ],
)
