"""Google Search Console integration manifest."""
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
    name="google_search_console",
    display_name="Google Search Console",
    description="Access Google Search Console data for search analytics and URL indexing",
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-search-console",
    app_url="https://search.google.com/search-console",
    categories=["Marketing & Advertising", "SEO", "Marketing", "Developer Tools & Infrastructure"],
    actions=[
        ActionDefinition(
            name="retrieve_site_performance_data",
            description="Fetches search analytics from Google Search Console for a verified site",
            parameters={
                "site_url": ParameterDef(
                    type="string",
                    description="The site URL as registered in Search Console (e.g. 'sc-domain:example.com' or 'https://example.com/')",
                    required=True,
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Start date in YYYY-MM-DD format",
                    required=True,
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="End date in YYYY-MM-DD format",
                    required=True,
                ),
                "dimensions": ParameterDef(
                    type="array",
                    description="Dimensions to group results by. Allowed values: country, device, page, query, searchAppearance, date",
                ),
                "search_type": ParameterDef(
                    type="string",
                    description="Type of search. Allowed values: web, image, video, news, googleNews, discover",
                    default="web",
                ),
                "aggregation_type": ParameterDef(
                    type="string",
                    description="Aggregation type. Allowed values: auto, byPage",
                ),
                "row_limit": ParameterDef(
                    type="integer",
                    description="Maximum number of rows to return",
                    default=10,
                ),
                "start_row": ParameterDef(
                    type="integer",
                    description="Start row for pagination (zero-based)",
                ),
                "subdomain_filter": ParameterDef(
                    type="string",
                    description="Filter results to a specific subdomain when using a domain property (e.g. 'https://subdomain.example.com')",
                ),
                "filter_dimension": ParameterDef(
                    type="string",
                    description="Dimension to filter by when subdomain_filter is used. Allowed values: country, device, page, query",
                    default="page",
                ),
                "filter_operator": ParameterDef(
                    type="string",
                    description="Filter operator. Allowed values: contains, equals, notContains, notEquals, includingRegex, excludingRegex",
                    default="contains",
                ),
                "advanced_dimension_filters": ParameterDef(
                    type="object",
                    description="Custom dimension filter groups following the Search Console API structure (JSON object)",
                ),
                "data_state": ParameterDef(
                    type="string",
                    description="Data state to use. Allowed values: all, final",
                    default="final",
                ),
            },
        ),
        ActionDefinition(
            name="submit_url_for_indexing",
            description="Sends a URL update notification to the Google Indexing API",
            parameters={
                "site_url": ParameterDef(
                    type="string",
                    description="The URL to submit for indexing (must be a canonical URL verified in Google Search Console)",
                    required=True,
                ),
                "notification_type": ParameterDef(
                    type="string",
                    description="Type of notification. Allowed values: URL_UPDATED (content updated), URL_DELETED (page removed)",
                    default="URL_UPDATED",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_SEARCH_CONSOLE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_SEARCH_CONSOLE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/webmasters.readonly",
                    "https://www.googleapis.com/auth/indexing",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://searchconsole.googleapis.com/webmasters/v3/sites",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["siteEntry"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing verified sites",
            ),
        ),
    ],
)
