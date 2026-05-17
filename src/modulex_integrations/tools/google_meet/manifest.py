"""Google Meet integration manifest."""
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
    name="google_meet",
    display_name="Google Meet",
    description="Schedule Google Meet video conferences via Google Calendar events.",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:google_meet-themed",
    app_url="https://meet.google.com",
    categories=["Communication", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="schedule_meeting",
            description=(
                "Creates a new event in Google Calendar with a Google Meet "
                "video conference link attached."
            ),
            parameters={
                "event_start_date": ParameterDef(
                    type="string",
                    description=(
                        "For all-day events use yyyy-mm-dd. For timed events use "
                        "RFC3339 (yyyy-mm-ddThh:mm:ss+01:00). A time zone offset is "
                        "required unless time_zone is set."
                    ),
                    required=True,
                ),
                "event_end_date": ParameterDef(
                    type="string",
                    description=(
                        "For all-day events use yyyy-mm-dd. For timed events use "
                        "RFC3339 (yyyy-mm-ddThh:mm:ss+01:00). A time zone offset is "
                        "required unless time_zone is set."
                    ),
                    required=True,
                ),
                "calendar_id": ParameterDef(
                    type="string",
                    description=(
                        "Calendar to create the event on. Defaults to 'primary' "
                        "(the authenticated user's primary calendar)."
                    ),
                    default="primary",
                ),
                "summary": ParameterDef(
                    type="string",
                    description="Title of the event (e.g. 'Weekly sync').",
                ),
                "location": ParameterDef(
                    type="string",
                    description="Physical or virtual location of the event.",
                ),
                "description": ParameterDef(
                    type="string",
                    description="Long-form description of the event.",
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="List of attendee email addresses to invite.",
                ),
                "recurrence": ParameterDef(
                    type="array",
                    description=(
                        "RRULE strings describing recurrence (e.g. "
                        "'RRULE:FREQ=DAILY;INTERVAL=2')."
                    ),
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description=(
                        "IANA time zone name used for start/end (e.g. "
                        "'America/Los_Angeles'). Defaults to the calendar's time zone."
                    ),
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description=(
                        "Whether to notify attendees: 'all', 'externalOnly', or 'none'."
                    ),
                ),
                "send_notifications": ParameterDef(
                    type="boolean",
                    description="Whether to send notifications about the event update.",
                ),
                "color_id": ParameterDef(
                    type="string",
                    description=(
                        "Color ID for the event. Use list_color_id_options to discover "
                        "valid values."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_color_id_options",
            description=(
                "Retrieves the available event color options (id, background, "
                "foreground) from Google Calendar."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_MEET_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google Cloud OAuth 2.0 Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_MEET_OAUTH2_CLIENT_SECRET",
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
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/calendar.events",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["kind"],
                ),
                cost_level="free",
                description=(
                    "Validates the OAuth token by listing one entry from the user's "
                    "calendar list."
                ),
            ),
        ),
    ],
)
