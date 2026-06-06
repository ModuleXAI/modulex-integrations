"""Google Analytics integration manifest."""
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
    name="google_analytics",
    display_name="Google Analytics",
    description=(
        "Manage Google Analytics 4 properties, list accounts, configure key "
        "events, and run analytics reports against the Google Analytics Admin "
        "and Data APIs."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-analytics",
    app_url="https://analytics.google.com",
    categories=[
        "Analytics & Data",
        "Analytics & Reporting",
        "Marketing",
        "Productivity & Collaboration",
    ],
    actions=[
        ActionDefinition(
            name="list_account_options",
            description=(
                "List Google Analytics accounts available to the authenticated "
                "user via the Admin API (/accounts endpoint)."
            ),
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description=(
                        "Maximum number of accounts to return per page. The "
                        "service may return fewer than this value. If "
                        "unspecified, at most 50 accounts are returned (max 200)."
                    ),
                    required=False,
                    default=50,
                ),
                "page_token": ParameterDef(
                    type="string",
                    description=(
                        "Optional page token from a previous response, used "
                        "to retrieve the next page of accounts."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="list_property_options",
            description=(
                "List GA4 properties visible to the authenticated user by "
                "flattening the propertySummaries returned from the Admin API "
                "/accountSummaries endpoint."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="create_ga4_property",
            description=(
                "Create a new GA4 property under an existing Google Analytics "
                "account via the Admin API (POST /properties)."
            ),
            parameters={
                "account": ParameterDef(
                    type="string",
                    description=(
                        "The parent account resource name, e.g. "
                        "'accounts/123456789'. Use list_account_options to "
                        "discover available accounts."
                    ),
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description=(
                        "Human-readable display name for the new property. "
                        "Max 100 UTF-16 code units."
                    ),
                    required=True,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description=(
                        "Reporting time zone for the property. Must be a valid "
                        "IANA timezone identifier, e.g. 'America/Los_Angeles', "
                        "'Europe/London', 'Asia/Tokyo'."
                    ),
                    required=True,
                ),
                "industry_category": ParameterDef(
                    type="string",
                    description=(
                        "Industry category associated with the property. "
                        "Valid values include AUTOMOTIVE, FINANCE, HEALTHCARE, "
                        "TECHNOLOGY, TRAVEL, ARTS_AND_ENTERTAINMENT, GAMES, "
                        "SHOPPING, JOBS_AND_EDUCATION, and others; pass "
                        "INDUSTRY_CATEGORY_UNSPECIFIED if unsure."
                    ),
                    required=False,
                    default=None,
                ),
                "currency_code": ParameterDef(
                    type="string",
                    description=(
                        "ISO 4217 currency code used in reports involving "
                        "monetary values, e.g. 'USD', 'EUR', 'JPY'."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="create_key_event",
            description=(
                "Create a new GA4 key event (conversion) on a property via the "
                "Admin API (POST /{parent}/keyEvents)."
            ),
            parameters={
                "parent": ParameterDef(
                    type="string",
                    description=(
                        "Parent property resource name where the key event "
                        "will be created. Format: 'properties/123'."
                    ),
                    required=True,
                ),
                "event_name": ParameterDef(
                    type="string",
                    description=(
                        "Immutable event name for this key event. "
                        "Examples: 'click', 'purchase', 'sign_up'."
                    ),
                    required=True,
                ),
                "counting_method": ParameterDef(
                    type="string",
                    description=(
                        "Method by which the key event is counted across "
                        "multiple events within a session. Valid values: "
                        "ONCE_PER_EVENT, ONCE_PER_SESSION, or "
                        "COUNTING_METHOD_UNSPECIFIED."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="run_report",
            description=(
                "Run a Universal Analytics (v4 Reporting API) report against a "
                "given view ID. Note: Universal Analytics was sunset July 2024 "
                "by Google; use run_report_in_ga4 for new GA4 reports."
            ),
            parameters={
                "view_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the Universal Analytics view to query. Found in "
                        "the legacy Google Analytics Admin UI under View "
                        "Settings."
                    ),
                    required=True,
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Start date in YYYY-MM-DD format.",
                    required=True,
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="End date in YYYY-MM-DD format.",
                    required=True,
                ),
                "metrics": ParameterDef(
                    type="array",
                    description=(
                        "List of metric expression strings (each becomes a "
                        "{expression: <metric>} entry), e.g. "
                        "['ga:sessions', 'ga:pageviews']."
                    ),
                    required=True,
                ),
                "dimensions": ParameterDef(
                    type="array",
                    description=(
                        "Optional list of dimension name strings (each becomes "
                        "a {name: <dimension>} entry), e.g. "
                        "['ga:country', 'ga:browser']."
                    ),
                    required=False,
                    default=None,
                ),
            },
        ),
        ActionDefinition(
            name="run_report_in_ga4",
            description=(
                "Run a GA4 Data API report against a GA4 property "
                "(POST /properties/{property}:runReport)."
            ),
            parameters={
                "property": ParameterDef(
                    type="string",
                    description=(
                        "GA4 property identifier. Accepts either the bare "
                        "numeric ID ('123456789') or the full resource path "
                        "('properties/123456789'); only the numeric ID is sent "
                        "in the URL."
                    ),
                    required=True,
                ),
                "start_date": ParameterDef(
                    type="string",
                    description="Start date in YYYY-MM-DD format.",
                    required=True,
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="End date in YYYY-MM-DD format.",
                    required=True,
                ),
                "metrics": ParameterDef(
                    type="array",
                    description=(
                        "List of metric name strings (each becomes a "
                        "{name: <metric>} entry), e.g. "
                        "['activeUsers', 'screenPageViews']."
                    ),
                    required=True,
                ),
                "dimensions": ParameterDef(
                    type="array",
                    description=(
                        "Optional list of dimension name strings (each becomes "
                        "a {name: <dimension>} entry), e.g. "
                        "['country', 'deviceCategory']."
                    ),
                    required=False,
                    default=None,
                ),
                "dimension_filter": ParameterDef(
                    type="object",
                    description=(
                        "Optional GA4 FilterExpression object restricting "
                        "which dimension values appear in the report. See the "
                        "Google Analytics Data API v1 docs for the schema."
                    ),
                    required=False,
                    default=None,
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
                    name="GOOGLE_ANALYTICS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google Cloud OAuth 2.0 Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format=(
                        "1234567890-abcdefghijklmnop.apps.googleusercontent.com"
                    ),
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_ANALYTICS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google Cloud OAuth 2.0 Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                scopes=[
                    "https://www.googleapis.com/auth/analytics.edit",
                    "https://www.googleapis.com/auth/analytics.readonly",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://analyticsadmin.googleapis.com/v1beta/accountSummaries",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=[],
                ),
                cost_level="free",
                description=(
                    "Validates the OAuth token by listing account summaries "
                    "from the Google Analytics Admin API."
                ),
            ),
        ),
    ],
)
