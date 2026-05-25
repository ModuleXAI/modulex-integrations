"""Sentry integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="sentry",
    display_name="Sentry",
    description="Error tracking and performance monitoring platform",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:sentry-themed",
    app_url="https://sentry.io",
    categories=["Developer Tools & Infrastructure", "monitoring", "error-tracking"],
    actions=[
        ActionDefinition(
            name="list_issue_events",
            description="Return a list of events bound to an issue",
            parameters={
                "issue_id": ParameterDef(
                    type="string",
                    description="The ID of the issue whose events to list",
                    required=True,
                ),
                "full": ParameterDef(
                    type="boolean",
                    description="If true, include the full event body including the stacktrace",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_project_events",
            description="Return a list of events bound to a project",
            parameters={
                "organization_slug": ParameterDef(
                    type="string",
                    description="The slug of the organization",
                    required=True,
                ),
                "project_slug": ParameterDef(
                    type="string",
                    description="The slug of the project",
                    required=True,
                ),
                "full": ParameterDef(
                    type="boolean",
                    description="If true, include the full event body including the stacktrace",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="list_project_issues",
            description="Return a list of issues bound to a project",
            parameters={
                "organization_slug": ParameterDef(
                    type="string",
                    description="The slug of the organization",
                    required=True,
                ),
                "project_slug": ParameterDef(
                    type="string",
                    description="The slug of the project",
                    required=True,
                ),
                "query": ParameterDef(
                    type="string",
                    description="A Sentry structured search query. If not provided an implied 'is:unresolved' is assumed",
                ),
                "stats_period": ParameterDef(
                    type="string",
                    description="An optional stat period (e.g. '24h', '14d')",
                ),
                "short_id_lookup": ParameterDef(
                    type="boolean",
                    description="If true, short IDs are also looked up by this function",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return",
                    default=100,
                ),
            },
        ),
        ActionDefinition(
            name="update_issue",
            description="Update an individual issue's attributes",
            parameters={
                "issue_id": ParameterDef(
                    type="string",
                    description="The ID of the issue to update",
                    required=True,
                ),
                "status": ParameterDef(
                    type="string",
                    description="New status for the issue: resolved, resolvedInNextRelease, unresolved, ignored",
                ),
                "assigned_to": ParameterDef(
                    type="string",
                    description="The actor ID or username to assign to this issue",
                ),
                "has_seen": ParameterDef(
                    type="boolean",
                    description="Changes the flag indicating if the user has seen the event",
                ),
                "is_bookmarked": ParameterDef(
                    type="boolean",
                    description="Changes the bookmark flag",
                ),
                "is_public": ParameterDef(
                    type="boolean",
                    description="Sets the issue to public or private",
                ),
            },
        ),
    ],
    auth_schemas=[
        BearerTokenAuthSchema(
            display_name="Auth Token",
            description="Use your Sentry Auth Token (internal integration token or user auth token)",
            setup_instructions=[
                "Go to Sentry Settings -> Developer Settings -> Internal Integrations",
                "Create a new internal integration or use an existing one",
                "Copy the token from the integration's credentials",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SENTRY_AUTH_TOKEN",
                    display_name="Auth Token",
                    description="Your Sentry Auth Token",
                    required=True,
                    sensitive=True,
                    sample_format="sntrys_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://docs.sentry.io/api/guides/create-auth-token/",
                ),
                EnvVar(
                    name="SENTRY_BASE_URL",
                    display_name="Sentry Base URL",
                    description=(
                        "Sentry API base URL. Use https://sentry.io for "
                        "US SaaS (default), https://de.sentry.io for "
                        "Germany SaaS, or your self-hosted Sentry URL."
                    ),
                    required=True,
                    sensitive=False,
                    sample_format="https://sentry.io",
                    about_url="https://docs.sentry.io/product/accounts/saas-data-routing/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="{base_url}/api/0/",
                method="GET",
                headers={"Authorization": "Bearer {token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                ),
                cost_level="free",
                description=(
                    "Validates the token by hitting the Sentry API root on "
                    "the configured base URL (supports US/DE SaaS and "
                    "self-hosted instances)"
                ),
            ),
        ),
    ],
)
