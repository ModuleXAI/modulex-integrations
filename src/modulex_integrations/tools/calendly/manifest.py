"""Calendly integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
    EnvVar,
    IntegrationManifest,
    OAuth2AuthSchema,
    OAuthConfig,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


def _users_me_test_endpoint(placeholder: str) -> TestEndpoint:
    return TestEndpoint(
        url="https://api.calendly.com/users/me",
        method="GET",
        headers={"Authorization": f"Bearer {{{placeholder}}}"},
        success_indicators=SuccessIndicators(status_codes=[200]),
    )


def _pagination_params() -> dict[str, ParameterDef]:
    return {
        "count": ParameterDef(
            type="integer",
            description="Number of results to return (max 100)",
            default=20,
        ),
        "page_token": ParameterDef(
            type="string", description="Token for pagination"
        ),
    }


manifest = IntegrationManifest(
    name="calendly",
    display_name="Calendly",
    description=(
        "Calendly scheduling platform integration for managing events, "
        "invitees, event types, and scheduling links. Automate meeting "
        "scheduling workflows and access scheduling data."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="simple-icons:calendly",
    app_url="https://calendly.com",
    categories=["Productivity", "calendar", "productivity", "meetings"],
    actions=[
        ActionDefinition(
            name="get_current_user",
            description=(
                "Get information about the currently authenticated Calendly "
                "user including name, email, and organization"
            ),
            parameters={},
        ),
        ActionDefinition(
            name="list_events",
            description=(
                "List scheduled events for a user or organization with "
                "filtering options"
            ),
            parameters={
                "user": ParameterDef(
                    type="string",
                    description=(
                        "User URI to filter events. Defaults to the "
                        "authenticated user."
                    ),
                ),
                "organization": ParameterDef(
                    type="string", description="Organization URI to filter events"
                ),
                "invitee_email": ParameterDef(
                    type="string", description="Filter by invitee email"
                ),
                "status": ParameterDef(
                    type="string",
                    description="Filter by event status ('active' or 'canceled')",
                ),
                "min_start_time": ParameterDef(
                    type="string",
                    description="Minimum start time (ISO 8601)",
                ),
                "max_start_time": ParameterDef(
                    type="string",
                    description="Maximum start time (ISO 8601)",
                ),
                **_pagination_params(),
                "sort": ParameterDef(
                    type="string",
                    description="Sort order ('start_time:asc' or 'start_time:desc')",
                ),
            },
        ),
        ActionDefinition(
            name="get_event",
            description="Get detailed information about a specific scheduled event",
            parameters={
                "event_uuid": ParameterDef(
                    type="string",
                    description="The UUID of the event to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_event_invitees",
            description="List all invitees for a specific scheduled event",
            parameters={
                "event_uuid": ParameterDef(
                    type="string",
                    description="The UUID of the event",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string", description="Filter by invitee email"
                ),
                "status": ParameterDef(
                    type="string",
                    description="Filter by invitee status ('active' or 'canceled')",
                ),
                **_pagination_params(),
                "sort": ParameterDef(
                    type="string",
                    description="Sort order ('created_at:asc' or 'created_at:desc')",
                ),
            },
        ),
        ActionDefinition(
            name="list_event_types",
            description="List all event types for a user or organization",
            parameters={
                "user": ParameterDef(
                    type="string", description="User URI to filter event types"
                ),
                "organization": ParameterDef(
                    type="string",
                    description="Organization URI to filter event types",
                ),
                "active": ParameterDef(
                    type="boolean", description="Filter by active status"
                ),
                **_pagination_params(),
                "sort": ParameterDef(
                    type="string",
                    description="Sort order ('name:asc' or 'name:desc')",
                ),
            },
        ),
        ActionDefinition(
            name="create_scheduling_link",
            description="Create a single-use scheduling link for an event type",
            parameters={
                "owner": ParameterDef(
                    type="string",
                    description="URI or UUID of the event type",
                    required=True,
                ),
                "max_event_count": ParameterDef(
                    type="integer",
                    description="Maximum events that can be scheduled with this link",
                    default=1,
                ),
            },
        ),
        ActionDefinition(
            name="create_invitee_no_show",
            description="Mark an invitee as a no-show for a scheduled event",
            parameters={
                "invitee_uri": ParameterDef(
                    type="string",
                    description="URI of the invitee to mark as no-show",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_user_availability_schedules",
            description="List availability schedules for a specific user",
            parameters={
                "user": ParameterDef(
                    type="string",
                    description="URI or UUID of the user",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_organization_members",
            description="List members of an organization",
            parameters={
                "organization": ParameterDef(
                    type="string",
                    description=(
                        "Organization URI. Defaults to the authenticated "
                        "user's organization."
                    ),
                ),
                "user": ParameterDef(
                    type="string", description="Filter by user URI"
                ),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="list_groups",
            description="List groups within an organization",
            parameters={
                "organization": ParameterDef(
                    type="string",
                    description="Organization URI to list groups for",
                    required=True,
                ),
                **_pagination_params(),
            },
        ),
        ActionDefinition(
            name="list_webhook_subscriptions",
            description="List webhook subscriptions for an organization or user",
            parameters={
                "organization": ParameterDef(
                    type="string",
                    description="Organization URI",
                    required=True,
                ),
                "scope": ParameterDef(
                    type="string",
                    description="Scope ('organization' or 'user')",
                    required=True,
                ),
                "user": ParameterDef(
                    type="string",
                    description="User URI (required if scope is 'user')",
                ),
                **_pagination_params(),
                "sort": ParameterDef(
                    type="string",
                    description="Sort order ('created_at:asc' or 'created_at:desc')",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth 2.0 Authentication",
            description="Authenticate using Calendly OAuth 2.0 flow",
            setup_environment_variables=[
                EnvVar(
                    name="CALENDLY_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Calendly App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://calendly.com/integrations/api_webhooks",
                ),
                EnvVar(
                    name="CALENDLY_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Calendly App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://calendly.com/integrations/api_webhooks",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://auth.calendly.com/oauth/authorize",
                token_url="https://auth.calendly.com/oauth/token",
                scopes=["default"],
                token_auth_method="body",
            ),
            test_endpoint=_users_me_test_endpoint("access_token"),
        ),
        BearerTokenAuthSchema(
            display_name="Personal Access Token",
            description="Authenticate using a Calendly Personal Access Token",
            setup_environment_variables=[
                EnvVar(
                    name="CALENDLY_API_TOKEN",
                    display_name="Calendly Personal Access Token",
                    description="Your Calendly Personal Access Token",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=_users_me_test_endpoint("token"),
        ),
    ],
)
