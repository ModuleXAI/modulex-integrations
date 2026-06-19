"""Google Calendar integration manifest."""
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
    name="google_calendar",
    display_name="Google Calendar",
    description="Manage Google Calendar events, calendars, and availability via the Google Calendar v3 REST API.",
    version="1.0.0",
    author="ModuleX",
    logo="logos:google-calendar",
    app_url="https://calendar.google.com",
    categories=["Scheduling & Events", "Productivity & Collaboration", "Scheduling"],
    actions=[
        ActionDefinition(
            name="add_attendees_to_event",
            description="Add attendees to an existing Google Calendar event.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar, or a calendar email/ID).",
                    default="primary",
                    required=False,
                ),
                "event_id": ParameterDef(
                    type="string",
                    description="ID of the event to update.",
                    required=True,
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="List of attendee email addresses to add (existing attendees are preserved).",
                    required=True,
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description="Whether to send notifications about the update. One of: all, externalOnly, none.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="create_event",
            description="Create a new event in a Google Calendar.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar, or a calendar email/ID).",
                    default="primary",
                    required=False,
                ),
                "summary": ParameterDef(
                    type="string",
                    description="Event title.",
                    required=True,
                ),
                "event_start_date": ParameterDef(
                    type="string",
                    description="Event start. For all-day events: yyyy-mm-dd. For timed events: RFC3339, e.g. 2025-01-15T10:00:00-05:00.",
                    required=True,
                ),
                "event_end_date": ParameterDef(
                    type="string",
                    description="Event end. Same formats as event_start_date.",
                    required=True,
                ),
                "location": ParameterDef(
                    type="string",
                    description="Event location.",
                    required=False,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Event description.",
                    required=False,
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="List of attendee email addresses.",
                    required=False,
                ),
                "color_id": ParameterDef(
                    type="string",
                    description="Color ID for the event. See list_color_id_options for valid values.",
                    required=False,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone name for the event (e.g. 'America/New_York'). Defaults to the calendar's time zone.",
                    required=False,
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description="Whether to send invitations. One of: all, externalOnly, none.",
                    required=False,
                ),
                "create_meet_room": ParameterDef(
                    type="boolean",
                    description="Whether to attach a Google Meet conference link to this event.",
                    default=False,
                    required=False,
                ),
                "visibility": ParameterDef(
                    type="string",
                    description="Event visibility. One of: default, public, private, confidential.",
                    required=False,
                ),
                "repeat_frequency": ParameterDef(
                    type="string",
                    description="Recurrence frequency. One of: DAILY, WEEKLY, MONTHLY, YEARLY.",
                    required=False,
                ),
                "repeat_interval": ParameterDef(
                    type="integer",
                    description="Recurrence interval (1 = every period, 2 = every other, ...). Defaults to 1.",
                    required=False,
                ),
                "repeat_specific_days": ParameterDef(
                    type="array",
                    description="Two-letter day codes for WEEKLY recurrence (SU,MO,TU,WE,TH,FR,SA).",
                    required=False,
                ),
                "repeat_until": ParameterDef(
                    type="string",
                    description="End date for recurrence (yyyy-mm-dd). Mutually exclusive with repeat_times.",
                    required=False,
                ),
                "repeat_times": ParameterDef(
                    type="integer",
                    description="Number of occurrences. Mutually exclusive with repeat_until.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="delete_event",
            description="Delete an event from a Google Calendar.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "event_id": ParameterDef(
                    type="string",
                    description="ID of the event to delete.",
                    required=True,
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description="Whether to send cancellation notifications. One of: all, externalOnly, none.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_calendar",
            description="Retrieve metadata for a Google Calendar.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_current_user",
            description="Retrieve the authenticated user's primary calendar, calendar list, settings (timezone/locale), and color palette.",
            parameters={},
        ),
        ActionDefinition(
            name="get_date_time",
            description="Return the current date/time, IANA timezone, UTC offset, ISO string, and RFC3339 timestamp. Useful for grounding scheduling decisions.",
            parameters={},
        ),
        ActionDefinition(
            name="get_event",
            description="Retrieve a single event from a Google Calendar.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "event_id": ParameterDef(
                    type="string",
                    description="ID of the event to retrieve.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_calendars",
            description="List calendars the authenticated user can access.",
            parameters={},
        ),
        ActionDefinition(
            name="list_color_id_options",
            description="List available color ID options for events, with hex backgrounds.",
            parameters={},
        ),
        ActionDefinition(
            name="list_event_instances",
            description="List individual instances of a recurring event.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "event_id": ParameterDef(
                    type="string",
                    description="ID of the recurring event.",
                    required=True,
                ),
                "max_attendees": ParameterDef(
                    type="integer",
                    description="Maximum attendees per instance to include.",
                    required=False,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of instances to return across paged calls.",
                    required=False,
                ),
                "show_deleted": ParameterDef(
                    type="boolean",
                    description="Include cancelled instances.",
                    required=False,
                ),
                "time_min": ParameterDef(
                    type="string",
                    description="Lower bound (RFC3339) for instance start times.",
                    required=False,
                ),
                "time_max": ParameterDef(
                    type="string",
                    description="Upper bound (RFC3339) for instance start times.",
                    required=False,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone used in the response.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_events",
            description="List events on a Google Calendar, with optional filters and pagination.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "i_cal_uid": ParameterDef(
                    type="string",
                    description="Specifies an iCalendar UID to filter by.",
                    required=False,
                ),
                "max_attendees": ParameterDef(
                    type="integer",
                    description="Maximum attendees per event to include.",
                    required=False,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of events to return across paged calls.",
                    required=False,
                ),
                "order_by": ParameterDef(
                    type="string",
                    description="Sort order. One of: startTime, updated. startTime requires single_events=true.",
                    required=False,
                ),
                "private_extended_property": ParameterDef(
                    type="string",
                    description="propertyName=value constraint on private extended properties.",
                    required=False,
                ),
                "q": ParameterDef(
                    type="string",
                    description="Free-text search across event fields.",
                    required=False,
                ),
                "shared_extended_property": ParameterDef(
                    type="string",
                    description="propertyName=value constraint on shared extended properties.",
                    required=False,
                ),
                "show_deleted": ParameterDef(
                    type="boolean",
                    description="Include cancelled events.",
                    required=False,
                ),
                "show_hidden_invitations": ParameterDef(
                    type="boolean",
                    description="Include hidden invitations.",
                    required=False,
                ),
                "single_events": ParameterDef(
                    type="boolean",
                    description="Expand recurring events into individual instances.",
                    required=False,
                ),
                "time_max": ParameterDef(
                    type="string",
                    description="Upper bound (RFC3339) for event start times.",
                    required=False,
                ),
                "time_min": ParameterDef(
                    type="string",
                    description="Lower bound (RFC3339) for event start times.",
                    required=False,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone used in the response.",
                    required=False,
                ),
                "updated_min": ParameterDef(
                    type="string",
                    description="Lower bound (RFC3339) for event last-modified time.",
                    required=False,
                ),
                "event_types": ParameterDef(
                    type="array",
                    description="Filter by event type. Values: default, focusTime, outOfOffice, workingLocation.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="query_free_busy_calendars",
            description="Query free/busy time blocks across one or more calendars over a date range.",
            parameters={
                "calendar_ids": ParameterDef(
                    type="array",
                    description="List of calendar IDs to query (use 'primary' for the user's primary calendar).",
                    default=["primary"],
                    required=True,
                ),
                "time_min": ParameterDef(
                    type="string",
                    description="Start of the query window (RFC3339).",
                    required=True,
                ),
                "time_max": ParameterDef(
                    type="string",
                    description="End of the query window (RFC3339).",
                    required=True,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone for the response.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="quick_add_event",
            description="Create an event from a natural-language string (Google parses date/time/title).",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "text": ParameterDef(
                    type="string",
                    description="Natural-language event description, e.g. 'Meet with Sarah at 3pm Friday'.",
                    required=True,
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="Optional list of attendee email addresses to add after parsing.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_event",
            description="Update an existing event on a Google Calendar.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "event_id": ParameterDef(
                    type="string",
                    description="ID of the event to update.",
                    required=True,
                ),
                "summary": ParameterDef(
                    type="string",
                    description="New event title.",
                    required=False,
                ),
                "event_start_date": ParameterDef(
                    type="string",
                    description="New start (yyyy-mm-dd for all-day, or RFC3339 for timed).",
                    required=False,
                ),
                "event_end_date": ParameterDef(
                    type="string",
                    description="New end (yyyy-mm-dd for all-day, or RFC3339 for timed).",
                    required=False,
                ),
                "location": ParameterDef(
                    type="string",
                    description="New event location.",
                    required=False,
                ),
                "description": ParameterDef(
                    type="string",
                    description="New event description.",
                    required=False,
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="Replacement list of attendee email addresses.",
                    required=False,
                ),
                "color_id": ParameterDef(
                    type="string",
                    description="New color ID for the event.",
                    required=False,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone (defaults to the event's existing time zone).",
                    required=False,
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description="Whether to send notifications. One of: all, externalOnly, none.",
                    required=False,
                ),
                "repeat_frequency": ParameterDef(
                    type="string",
                    description="Updated recurrence frequency. One of: DAILY, WEEKLY, MONTHLY, YEARLY.",
                    required=False,
                ),
                "repeat_interval": ParameterDef(
                    type="integer",
                    description="Updated recurrence interval.",
                    required=False,
                ),
                "repeat_specific_days": ParameterDef(
                    type="array",
                    description="Two-letter day codes for WEEKLY recurrence.",
                    required=False,
                ),
                "repeat_until": ParameterDef(
                    type="string",
                    description="New end date for recurrence (yyyy-mm-dd).",
                    required=False,
                ),
                "repeat_times": ParameterDef(
                    type="integer",
                    description="New number of occurrences.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_event_instance",
            description="Update a single instance of a recurring event (changes apply only to that instance).",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "instance_id": ParameterDef(
                    type="string",
                    description="ID of the specific recurring-event instance to update.",
                    required=True,
                ),
                "summary": ParameterDef(
                    type="string",
                    description="New event title.",
                    required=False,
                ),
                "event_start_date": ParameterDef(
                    type="string",
                    description="New start (yyyy-mm-dd for all-day, or RFC3339 for timed).",
                    required=False,
                ),
                "event_end_date": ParameterDef(
                    type="string",
                    description="New end (yyyy-mm-dd for all-day, or RFC3339 for timed).",
                    required=False,
                ),
                "location": ParameterDef(
                    type="string",
                    description="New event location.",
                    required=False,
                ),
                "description": ParameterDef(
                    type="string",
                    description="New event description.",
                    required=False,
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="Replacement list of attendee email addresses.",
                    required=False,
                ),
                "color_id": ParameterDef(
                    type="string",
                    description="New color ID for the event instance.",
                    required=False,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone (defaults to the instance's existing time zone).",
                    required=False,
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description="Whether to send notifications. One of: all, externalOnly, none.",
                    required=False,
                ),
            },
        ),
        ActionDefinition(
            name="update_following_instances",
            description="Update all instances of a recurring event from a given instance forward by splitting the series.",
            parameters={
                "calendar_id": ParameterDef(
                    type="string",
                    description="Calendar identifier (use 'primary' for the user's primary calendar).",
                    default="primary",
                    required=False,
                ),
                "recurring_event_id": ParameterDef(
                    type="string",
                    description="ID of the parent recurring event.",
                    required=True,
                ),
                "instance_id": ParameterDef(
                    type="string",
                    description="ID of the instance from which the split begins (this and all following instances are updated).",
                    required=True,
                ),
                "summary": ParameterDef(
                    type="string",
                    description="New event title for the split series.",
                    required=False,
                ),
                "event_start_date": ParameterDef(
                    type="string",
                    description="New start (yyyy-mm-dd or RFC3339) for the split series.",
                    required=False,
                ),
                "event_end_date": ParameterDef(
                    type="string",
                    description="New end (yyyy-mm-dd or RFC3339) for the split series.",
                    required=False,
                ),
                "location": ParameterDef(
                    type="string",
                    description="New location for the split series.",
                    required=False,
                ),
                "description": ParameterDef(
                    type="string",
                    description="New description for the split series.",
                    required=False,
                ),
                "attendees": ParameterDef(
                    type="array",
                    description="Replacement list of attendee email addresses.",
                    required=False,
                ),
                "color_id": ParameterDef(
                    type="string",
                    description="New color ID for the split series.",
                    required=False,
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="IANA time zone for the split series.",
                    required=False,
                ),
                "send_updates": ParameterDef(
                    type="string",
                    description="Whether to send notifications. One of: all, externalOnly, none.",
                    required=False,
                ),
                "repeat_frequency": ParameterDef(
                    type="string",
                    description="Optional new recurrence frequency for the split series.",
                    required=False,
                ),
                "repeat_interval": ParameterDef(
                    type="integer",
                    description="Optional new recurrence interval for the split series.",
                    required=False,
                ),
                "repeat_until": ParameterDef(
                    type="string",
                    description="Optional new recurrence end date (yyyy-mm-dd).",
                    required=False,
                ),
                "repeat_times": ParameterDef(
                    type="integer",
                    description="Optional new occurrence count.",
                    required=False,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Google OAuth (recommended). Grants access to read and manage the user's calendars and events.",
            setup_environment_variables=[
                EnvVar(
                    name="GOOGLE_CALENDAR_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Google Cloud OAuth Client ID for the Calendar API.",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
                    about_url="https://console.cloud.google.com/apis/credentials",
                ),
                EnvVar(
                    name="GOOGLE_CALENDAR_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Google Cloud OAuth Client Secret for the Calendar API.",
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
                access_type="offline",
                prompt="consent",
                scopes=[
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/calendar.events",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://www.googleapis.com/calendar/v3/users/me/calendarList?maxResults=1",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["kind"],
                ),
                cost_level="free",
                description="Validates the OAuth token by listing one calendar from the user's calendar list.",
            ),
        ),
    ],
)
