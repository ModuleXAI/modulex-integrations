"""Ahrefs integration manifest."""
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
    name="ahrefs",
    display_name="Ahrefs",
    description="SEO toolset providing backlink analysis, referring domain data, and site explorer metrics via the Ahrefs REST API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:ahrefs-themed",
    app_url="https://ahrefs.com",
    categories=["SEO", "Marketing", "Web Search & Scraping"],
    actions=[
        ActionDefinition(
            name="get_backlinks",
            description="Get the backlinks for a domain or URL with details for the referring pages (e.g., anchor and page title)",
            parameters={
                "target": ParameterDef(
                    type="string",
                    description="Domain or URL to get backlinks for",
                    required=True,
                ),
                "select": ParameterDef(
                    type="array",
                    description="List of columns to return (e.g. url_from, url_to, ahrefs_rank, anchor, page_title)",
                    required=True,
                ),
                "mode": ParameterDef(
                    type="string",
                    description="Mode of operation: exact, domain, subdomains, or prefix",
                    default="domain",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of results to return",
                    default=1000,
                ),
            },
        ),
        ActionDefinition(
            name="get_backlinks_one_per_domain",
            description="Get one backlink with the highest ahrefs_rank per referring domain for a target URL or domain",
            parameters={
                "target": ParameterDef(
                    type="string",
                    description="Domain or URL to get backlinks for",
                    required=True,
                ),
                "select": ParameterDef(
                    type="array",
                    description="List of columns to return (e.g. url_from, url_to, ahrefs_rank, anchor, page_title)",
                    required=True,
                ),
                "mode": ParameterDef(
                    type="string",
                    description="Mode of operation: exact, domain, subdomains, or prefix",
                    default="domain",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of results to return",
                    default=1000,
                ),
            },
        ),
        ActionDefinition(
            name="get_referring_domains",
            description="Get the referring domains that contain backlinks to the target URL or domain",
            parameters={
                "target": ParameterDef(
                    type="string",
                    description="Domain or URL to get referring domains for",
                    required=True,
                ),
                "select": ParameterDef(
                    type="array",
                    description="List of columns to return for referring domains (e.g. domain, domain_rating, backlinks)",
                    required=True,
                ),
                "mode": ParameterDef(
                    type="string",
                    description="Mode of operation: exact, domain, subdomains, or prefix",
                    default="domain",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of results to return",
                    default=1000,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Ahrefs OAuth2 (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="AHREFS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Ahrefs OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://ahrefs.com/api/oauth",
                ),
                EnvVar(
                    name="AHREFS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Ahrefs OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://ahrefs.com/api/oauth",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://ahrefs.com/oauth2/authorize",
                token_url="https://ahrefs.com/oauth2/token",
                scopes=["api"],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.ahrefs.com/v3/site-explorer/all-backlinks",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                params={"target": "ahrefs.com", "select": "url_from", "mode": "domain", "limit": "1"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="minimal",
                description="Validates OAuth token by fetching a single backlink result",
            ),
        ),
    ],
)
