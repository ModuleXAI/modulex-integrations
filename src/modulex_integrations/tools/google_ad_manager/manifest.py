"""Google Ad Manager integration manifest."""
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
    name="google_ad_manager",
    display_name="Google Ad Manager",
    description="Programmatic advertising platform for managing ad inventory, reporting, and campaign delivery",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_ad_manager-themed",
    app_url="https://admanager.google.com",
    categories=["Marketing & Advertising", "Advertising", "Marketing"],
    actions=[
        ActionDefinition(
            name="create_report",
            description="Create a report in Google Ad Manager",
            parameters={
                "parent": ParameterDef(
                    type="string",
                    description="The parent resource where this Report will be created. Format: networks/{networkCode}",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Identifier. The resource name of the report. Format: networks/{networkCode}/reports/{reportId}",
                    required=True,
                ),
                "visibility": ParameterDef(
                    type="string",
                    description="The visibility of the report. Allowed values: HIDDEN, DRAFT, SAVED",
                    required=True,
                ),
                "dimensions": ParameterDef(
                    type="array",
                    description="The list of dimension identifiers to report on",
                    required=True,
                ),
                "metrics": ParameterDef(
                    type="array",
                    description="The list of metric identifiers to report on",
                    required=True,
                ),
                "report_type": ParameterDef(
                    type="string",
                    description="The type of this report. Allowed values: REPORT_TYPE_UNSPECIFIED, HISTORICAL",
                    required=True,
                ),
                "date_range": ParameterDef(
                    type="string",
                    description="The date range type of this report. Allowed values: fixed, relative",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="The display name of the report",
                ),
                "schedule_options": ParameterDef(
                    type="object",
                    description="The options for a scheduled report (ScheduleOptions schema)",
                ),
                "filters": ParameterDef(
                    type="array",
                    description="The filters for this report. Each element is a JSON object conforming to the Filter schema",
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="The time zone for the date range (IANA format). Defaults to publisher time zone",
                ),
                "currency_code": ParameterDef(
                    type="string",
                    description="ISO 4217 currency code. Defaults to publisher currency code",
                ),
                "custom_dimension_key_ids": ParameterDef(
                    type="array",
                    description="Custom Dimension keys for CUSTOM_DIMENSION_* dimensions",
                ),
                "line_item_custom_field_ids": ParameterDef(
                    type="array",
                    description="Custom field IDs for LINE_ITEM_CUSTOM_FIELD_* dimensions",
                ),
                "order_custom_field_ids": ParameterDef(
                    type="array",
                    description="Custom field IDs for ORDER_CUSTOM_FIELD_* dimensions",
                ),
                "creative_custom_field_ids": ParameterDef(
                    type="array",
                    description="Custom field IDs for CREATIVE_CUSTOM_FIELD_* dimensions",
                ),
                "time_period_column": ParameterDef(
                    type="string",
                    description="Time period column for comparison. Allowed values: TIME_PERIOD_COLUMN_UNSPECIFIED, TIME_PERIOD_COLUMN_DATE, TIME_PERIOD_COLUMN_WEEK, TIME_PERIOD_COLUMN_MONTH, TIME_PERIOD_COLUMN_QUARTER",
                ),
                "flags": ParameterDef(
                    type="array",
                    description="List of flags for this report (Flag schema objects)",
                ),
                "sorts": ParameterDef(
                    type="array",
                    description="Default sorts for this report (Sort schema objects)",
                ),
                "start_date_year": ParameterDef(
                    type="integer",
                    description="Year of the start date (1-9999). Required when date_range is 'fixed'",
                ),
                "start_date_month": ParameterDef(
                    type="integer",
                    description="Month of the start date (1-12). Required when date_range is 'fixed'",
                ),
                "start_date_day": ParameterDef(
                    type="integer",
                    description="Day of the start date (1-31). Required when date_range is 'fixed'",
                ),
                "end_date_year": ParameterDef(
                    type="integer",
                    description="Year of the end date (1-9999). Required when date_range is 'fixed'",
                ),
                "end_date_month": ParameterDef(
                    type="integer",
                    description="Month of the end date (1-12). Required when date_range is 'fixed'",
                ),
                "end_date_day": ParameterDef(
                    type="integer",
                    description="Day of the end date (1-31). Required when date_range is 'fixed'",
                ),
                "relative": ParameterDef(
                    type="string",
                    description="Relative date range identifier (e.g. TODAY, YESTERDAY, LAST_7_DAYS). Required when date_range is 'relative'",
                ),
                "comparison_date_range": ParameterDef(
                    type="string",
                    description="Comparison date range type. Allowed values: fixed, relative",
                ),
                "comparison_start_date_year": ParameterDef(
                    type="integer",
                    description="Year of comparison start date. Required when comparison_date_range is 'fixed'",
                ),
                "comparison_start_date_month": ParameterDef(
                    type="integer",
                    description="Month of comparison start date. Required when comparison_date_range is 'fixed'",
                ),
                "comparison_start_date_day": ParameterDef(
                    type="integer",
                    description="Day of comparison start date. Required when comparison_date_range is 'fixed'",
                ),
                "comparison_end_date_year": ParameterDef(
                    type="integer",
                    description="Year of comparison end date. Required when comparison_date_range is 'fixed'",
                ),
                "comparison_end_date_month": ParameterDef(
                    type="integer",
                    description="Month of comparison end date. Required when comparison_date_range is 'fixed'",
                ),
                "comparison_end_date_day": ParameterDef(
                    type="integer",
                    description="Day of comparison end date. Required when comparison_date_range is 'fixed'",
                ),
                "comparison_relative": ParameterDef(
                    type="string",
                    description="Relative comparison date range identifier (e.g. PREVIOUS_PERIOD, SAME_PERIOD_PREVIOUS_YEAR). Required when comparison_date_range is 'relative'",
                ),
            },
        ),
        ActionDefinition(
            name="list_network_options",
            description="Retrieve available network options for Google Ad Manager",
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_AD_MANAGER_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_AD_MANAGER_OAUTH2_CLIENT_SECRET",
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
                access_type="offline",
                prompt="consent",
                scopes=["https://www.googleapis.com/auth/admanager"],
            ),
            test_endpoint=TestEndpoint(
                url="https://admanager.googleapis.com/v1/networks",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["networks"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing accessible networks",
            ),
        ),
    ],
)
