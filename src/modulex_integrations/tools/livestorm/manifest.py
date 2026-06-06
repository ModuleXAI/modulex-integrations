"""Livestorm integration manifest."""
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
    name="livestorm",
    display_name="Livestorm",
    description="Video engagement platform for webinars and virtual events",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:livestorm-themed",
    app_url="https://livestorm.co",
    categories=["Scheduling & Events", "Marketing", "Webinars & Events"],
    actions=[
        ActionDefinition(
            name="create_event",
            description="Create a new event",
            parameters={
                "owner_id": ParameterDef(
                    type="string",
                    description="The ID of the user who owns the event",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the event",
                    required=True,
                ),
                "slug": ParameterDef(
                    type="string",
                    description="The slug of the event",
                ),
                "status": ParameterDef(
                    type="string",
                    description="The status of the event: draft, published",
                ),
                "description": ParameterDef(
                    type="string",
                    description="The HTML description of the event",
                ),
                "recording_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the event is recorded",
                ),
                "chat_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the chat is enabled",
                ),
                "everyone_can_speak": ParameterDef(
                    type="boolean",
                    description="Whether everyone can speak",
                ),
                "detailed_registration_page_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the detailed registration page is enabled",
                ),
                "light_registration_page_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the light registration page is enabled",
                ),
                "recording_public": ParameterDef(
                    type="boolean",
                    description="Whether the recording is public",
                ),
                "show_in_company_page": ParameterDef(
                    type="boolean",
                    description="Whether the event is shown in the company page",
                ),
                "polls_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the polls are enabled",
                ),
                "questions_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the questions are enabled",
                ),
            },
        ),
        ActionDefinition(
            name="get_event",
            description="Retrieve a single event",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The ID of the event",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_attendees_from_event",
            description="List all the people linked to all the sessions of an event",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The ID of the event",
                    required=True,
                ),
                "role_filter": ParameterDef(
                    type="string",
                    description="Filter by role: participant, team_member",
                ),
            },
        ),
        ActionDefinition(
            name="list_events",
            description="List the events of your workspace",
            parameters={
                "title_filter": ParameterDef(
                    type="string",
                    description="Filter events by title",
                ),
            },
        ),
        ActionDefinition(
            name="list_sessions",
            description="List all your event sessions",
            parameters={},
        ),
        ActionDefinition(
            name="register_someone_for_session",
            description="Register a new participant for a session",
            parameters={
                "session_id": ParameterDef(
                    type="string",
                    description="The ID of the session",
                    required=True,
                ),
                "referrer": ParameterDef(
                    type="string",
                    description="The referrer of the person registering",
                ),
                "utm_source": ParameterDef(
                    type="string",
                    description="The UTM source",
                ),
                "utm_medium": ParameterDef(
                    type="string",
                    description="The UTM medium",
                ),
                "utm_campaign": ParameterDef(
                    type="string",
                    description="The UTM campaign",
                ),
                "utm_term": ParameterDef(
                    type="string",
                    description="The UTM term",
                ),
                "utm_content": ParameterDef(
                    type="string",
                    description="The UTM content",
                ),
                "fields": ParameterDef(
                    type="object",
                    description="Registration fields as key-value pairs where key is the field ID and value is the field value",
                ),
            },
        ),
        ActionDefinition(
            name="update_event",
            description="Update an event with its full list of attributes",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The ID of the event",
                    required=True,
                ),
                "owner_id": ParameterDef(
                    type="string",
                    description="The ID of the user who owns the event",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the event",
                    required=True,
                ),
                "slug": ParameterDef(
                    type="string",
                    description="The slug of the event",
                    required=True,
                ),
                "status": ParameterDef(
                    type="string",
                    description="The status of the event: draft, published",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="The HTML description of the event",
                    required=True,
                ),
                "recording_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the event is recorded",
                    required=True,
                ),
                "chat_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the chat is enabled",
                    required=True,
                ),
                "everyone_can_speak": ParameterDef(
                    type="boolean",
                    description="Whether everyone can speak",
                    required=True,
                ),
                "detailed_registration_page_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the detailed registration page is enabled",
                    required=True,
                ),
                "light_registration_page_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the light registration page is enabled",
                    required=True,
                ),
                "recording_public": ParameterDef(
                    type="boolean",
                    description="Whether the recording is public",
                    required=True,
                ),
                "show_in_company_page": ParameterDef(
                    type="boolean",
                    description="Whether the event is shown in the company page",
                    required=True,
                ),
                "polls_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the polls are enabled",
                    required=True,
                ),
                "questions_enabled": ParameterDef(
                    type="boolean",
                    description="Whether the questions are enabled",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Livestorm OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="LIVESTORM_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Livestorm OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developers.livestorm.co",
                ),
                EnvVar(
                    name="LIVESTORM_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Livestorm OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developers.livestorm.co",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://app.livestorm.co/oauth/authorize",
                token_url="https://app.livestorm.co/oauth/token",
                scopes=[],
            ),
            test_endpoint=TestEndpoint(
                url="https://api.livestorm.co/v1/events",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Accept": "application/vnd.api+json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing events",
            ),
        ),
    ],
)
