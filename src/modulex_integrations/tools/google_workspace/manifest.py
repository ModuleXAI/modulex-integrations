"""Google Workspace integration manifest."""
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
    name="google_workspace",
    display_name="Google Workspace Admin",
    description="Retrieve admin audit activity reports from Google Workspace via the Admin SDK Reports API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_workspace-themed",
    app_url="https://workspace.google.com",
    categories=["Productivity & Collaboration", "admin", "enterprise"],
    actions=[
        ActionDefinition(
            name="list_activities_by_admin",
            description="Retrieve admin console activities for a specific administrator",
            parameters={
                "application_name": ParameterDef(
                    type="string",
                    description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep",
                    required=True,
                ),
                "user_key": ParameterDef(
                    type="string",
                    description="Profile ID or email of the administrator to filter activities for",
                    required=True,
                ),
                "event_name": ParameterDef(
                    type="string",
                    description="Name of the event to filter by",
                ),
                "end_time": ParameterDef(
                    type="string",
                    description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of activity records to return per page (default 1000)",
                ),
                "filters": ParameterDef(
                    type="string",
                    description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)",
                ),
            },
        ),
        ActionDefinition(
            name="list_activities_by_event_and_admin",
            description="Retrieve activities filtered by both a specific event name and administrator",
            parameters={
                "application_name": ParameterDef(
                    type="string",
                    description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep",
                    required=True,
                ),
                "event_name": ParameterDef(
                    type="string",
                    description="Name of the event to filter by",
                    required=True,
                ),
                "user_key": ParameterDef(
                    type="string",
                    description="Profile ID or email of the administrator to filter activities for",
                    required=True,
                ),
                "end_time": ParameterDef(
                    type="string",
                    description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of activity records to return per page (default 1000)",
                ),
                "filters": ParameterDef(
                    type="string",
                    description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)",
                ),
            },
        ),
        ActionDefinition(
            name="list_activities_by_event_name",
            description="Retrieve activities for all users filtered by a specific event name",
            parameters={
                "application_name": ParameterDef(
                    type="string",
                    description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep",
                    required=True,
                ),
                "event_name": ParameterDef(
                    type="string",
                    description="Name of the event to filter by",
                    required=True,
                ),
                "end_time": ParameterDef(
                    type="string",
                    description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of activity records to return per page (default 1000)",
                ),
                "filters": ParameterDef(
                    type="string",
                    description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)",
                ),
            },
        ),
        ActionDefinition(
            name="list_all_activities",
            description="Retrieve all administrative activities for the account",
            parameters={
                "application_name": ParameterDef(
                    type="string",
                    description="Application name to retrieve events for. Valid values: access_transparency, admin, calendar, chat, drive, gcp, gplus, groups, groups_enterprise, jamboard, login, meet, mobile, rules, saml, token, user_accounts, context_aware_access, chrome, data_studio, keep",
                    required=True,
                ),
                "end_time": ParameterDef(
                    type="string",
                    description="End of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Beginning of the time range in RFC 3339 format (e.g. 2010-10-28T10:26:35.000Z)",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of activity records to return per page (default 1000)",
                ),
                "filters": ParameterDef(
                    type="string",
                    description="Comma-separated event parameter filters (e.g. parameter_name relational_operator value)",
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
                    name="GOOGLE_WORKSPACE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_WORKSPACE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="GOCSPX-" + "x" * 28,
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://accounts.google.com/o/oauth2/v2/auth",
                token_url="https://oauth2.googleapis.com/token",
                access_type="offline",
                prompt="consent",
                scopes=[
                    "https://www.googleapis.com/auth/admin.reports.audit.readonly",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://admin.googleapis.com/admin/reports/v1/activity/users/all/applications/admin?maxResults=1",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["kind"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing one admin activity",
            ),
        ),
    ],
)
