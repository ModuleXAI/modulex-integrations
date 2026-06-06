"""Cal.com integration manifest."""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    ApiKeyAuthSchema,
    EnvVar,
    IntegrationManifest,
    ParameterDef,
    SuccessIndicators,
    TestEndpoint,
)

__all__ = ["manifest"]


manifest = IntegrationManifest(
    name="cal_com",
    display_name="Cal.com",
    description="Scheduling and booking management via the Cal.com v2 API",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:cal_com-themed",
    app_url="https://cal.com",
    categories=["Scheduling & Events", "Productivity & Collaboration", "scheduling", "calendar"],
    actions=[
        ActionDefinition(
            name="create_booking",
            description="Create a new booking on Cal.com",
            parameters={
                "booking_type": ParameterDef(
                    type="string",
                    description="Type of booking: booking, instant, or recurring",
                    required=True,
                ),
                "attendee_name": ParameterDef(
                    type="string",
                    description="Full name of the attendee",
                    required=True,
                ),
                "attendee_time_zone": ParameterDef(
                    type="string",
                    description="Time zone of the attendee, e.g. America/New_York",
                    required=True,
                ),
                "start": ParameterDef(
                    type="string",
                    description="Booking start time in ISO 8601 UTC format, e.g. 2024-08-13T09:00:00Z",
                    required=True,
                ),
                "attendee_email": ParameterDef(
                    type="string",
                    description="Email address of the attendee",
                ),
                "attendee_phone_number": ParameterDef(
                    type="string",
                    description="Phone number in international format, e.g. +919876543210",
                ),
                "attendee_language": ParameterDef(
                    type="string",
                    description="Language for the booking confirmation",
                ),
                "event_type_id": ParameterDef(
                    type="integer",
                    description="ID of the event type (alternative to slug-based identification)",
                ),
                "event_type_slug": ParameterDef(
                    type="string",
                    description="Slug of the event type (use with username or team_slug)",
                ),
                "username": ParameterDef(
                    type="string",
                    description="Username of the individual event owner",
                ),
                "team_slug": ParameterDef(
                    type="string",
                    description="Team slug for team event type identification",
                ),
                "organization_slug": ParameterDef(
                    type="string",
                    description="Organization slug for slug-based event type identification",
                ),
                "end_time": ParameterDef(
                    type="string",
                    description="Booking end time in ISO 8601 format",
                ),
                "length_in_minutes": ParameterDef(
                    type="integer",
                    description="Override the event type default duration in minutes",
                ),
                "guests": ParameterDef(
                    type="array",
                    description="Additional guest email addresses to invite",
                ),
                "location": ParameterDef(
                    type="string",
                    description="Meeting location type: attendeeAddress, attendeeDefined, attendeePhone, integration",
                ),
                "location_address": ParameterDef(
                    type="string",
                    description="Physical address if location is attendeeAddress",
                ),
                "location_value": ParameterDef(
                    type="string",
                    description="Location string if location is attendeeDefined",
                ),
                "location_phone": ParameterDef(
                    type="string",
                    description="Phone number if location is attendeePhone",
                ),
                "location_integration": ParameterDef(
                    type="string",
                    description="Video conferencing integration if location is integration",
                ),
                "recurrence_count": ParameterDef(
                    type="integer",
                    description="Number of occurrences for recurring booking type",
                ),
                "metadata": ParameterDef(
                    type="object",
                    description="Custom key-value metadata, e.g. {\"source\": \"website\"}",
                ),
                "booking_fields_responses": ParameterDef(
                    type="object",
                    description="Responses to custom booking form fields keyed by field slug",
                ),
                "allow_conflicts": ParameterDef(
                    type="boolean",
                    description="Bypass availability checks and allow double-booking",
                ),
                "allow_booking_out_of_bounds": ParameterDef(
                    type="boolean",
                    description="Allow booking outside the event type scheduling window",
                ),
                "email_verification_code": ParameterDef(
                    type="string",
                    description="Required when event type has email verification enabled",
                ),
            },
        ),
        ActionDefinition(
            name="delete_booking",
            description="Cancel an existing booking by its UID",
            parameters={
                "booking_id": ParameterDef(
                    type="string",
                    description="The UID of the booking to cancel",
                    required=True,
                ),
                "cancellation_reason": ParameterDef(
                    type="string",
                    description="The reason for cancelling the booking",
                ),
                "cancel_subsequent_bookings": ParameterDef(
                    type="boolean",
                    description="Whether to cancel all subsequent occurrences of a recurring booking",
                ),
            },
        ),
        ActionDefinition(
            name="get_all_bookings",
            description="Retrieve all bookings from Cal.com with optional filters",
            parameters={
                "max_pages": ParameterDef(
                    type="integer",
                    description="Maximum number of pages to fetch (1-500, default 50)",
                ),
                "status": ParameterDef(
                    type="array",
                    description="Filter by status: upcoming, recurring, past, cancelled, unconfirmed",
                ),
                "after_start": ParameterDef(
                    type="string",
                    description="Return bookings that start after this time (ISO 8601)",
                ),
                "before_end": ParameterDef(
                    type="string",
                    description="Return bookings that end before this time (ISO 8601)",
                ),
                "after_created_at": ParameterDef(
                    type="string",
                    description="Return bookings created after this time (ISO 8601)",
                ),
                "before_created_at": ParameterDef(
                    type="string",
                    description="Return bookings created before this time (ISO 8601)",
                ),
                "attendee_email": ParameterDef(
                    type="string",
                    description="Filter bookings by attendee email",
                ),
                "attendee_name": ParameterDef(
                    type="string",
                    description="Filter bookings by attendee name",
                ),
                "booking_uid": ParameterDef(
                    type="string",
                    description="Filter bookings by booking UID",
                ),
                "event_type_id": ParameterDef(
                    type="integer",
                    description="Filter bookings by event type ID",
                ),
                "sort_start": ParameterDef(
                    type="string",
                    description="Sort bookings by start time: asc or desc",
                ),
                "sort_end": ParameterDef(
                    type="string",
                    description="Sort bookings by end time: asc or desc",
                ),
                "sort_created": ParameterDef(
                    type="string",
                    description="Sort bookings by creation time: asc or desc",
                ),
            },
        ),
        ActionDefinition(
            name="get_bookable_slots",
            description="Retrieve available bookable slots between a datetime range",
            parameters={
                "start": ParameterDef(
                    type="string",
                    description="Start date/time in ISO 8601 format (UTC)",
                    required=True,
                ),
                "end": ParameterDef(
                    type="string",
                    description="End date/time in ISO 8601 format (UTC)",
                    required=True,
                ),
                "event_type_id": ParameterDef(
                    type="integer",
                    description="ID of the event type to get slots for",
                ),
                "event_type_slug": ParameterDef(
                    type="string",
                    description="Slug of the event type (requires username or team_slug)",
                ),
                "username": ParameterDef(
                    type="string",
                    description="Username of the individual event owner",
                ),
                "usernames": ParameterDef(
                    type="array",
                    description="List of at least 2 usernames for a dynamic event",
                ),
                "team_slug": ParameterDef(
                    type="string",
                    description="Slug of the team for team event type slot lookup",
                ),
                "organization_slug": ParameterDef(
                    type="string",
                    description="Organization slug for slug-based event type lookup",
                ),
                "time_zone": ParameterDef(
                    type="string",
                    description="The time zone for the slot lookup",
                ),
                "duration": ParameterDef(
                    type="integer",
                    description="Override the default slot duration in minutes",
                ),
                "format": ParameterDef(
                    type="string",
                    description="Response format: range (start and end) or time (start only)",
                ),
                "booking_uid_to_reschedule": ParameterDef(
                    type="string",
                    description="UID of the booking being rescheduled to exclude from busy calculations",
                ),
            },
        ),
        ActionDefinition(
            name="get_booking",
            description="Retrieve a booking by its UID",
            parameters={
                "booking_id": ParameterDef(
                    type="string",
                    description="The UID of the booking to retrieve",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_event_type_id_options",
            description="Retrieve available event types with their IDs",
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key",
            description="Authenticate using your Cal.com v2 API key",
            setup_instructions=[
                "Sign in to Cal.com at https://app.cal.com",
                "Navigate to Settings > Developer > API Keys",
                "Create a new API key or copy an existing one",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="CAL_COM_API_KEY",
                    display_name="Cal.com API Key",
                    description="Your Cal.com v2 API key from Settings > Developer > API Keys",
                    required=True,
                    sensitive=True,
                    sample_format="cal_live_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://app.cal.com/settings/developer/api-keys",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.cal.com/v2/event-types",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "cal-api-version": "2024-06-14",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["status"],
                ),
                cost_level="free",
                description="Validates the API key by listing event types",
            ),
        ),
    ],
)
