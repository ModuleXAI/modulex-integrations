"""Luma integration manifest."""
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
    name="luma",
    display_name="Luma",
    description="Event management platform for creating, managing, and tracking events and guests",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:luma-themed",
    app_url="https://lu.ma",
    categories=["Events", "Productivity & Collaboration", "Marketing"],
    actions=[
        ActionDefinition(
            name="create_event",
            description="Create an event on the connected Luma calendar",
            parameters={
                "name": ParameterDef(
                    type="string",
                    description="The event name",
                    required=True,
                ),
                "start_at": ParameterDef(
                    type="string",
                    description="The event start time as an ISO 8601 datetime, for example 2026-05-15T18:00:00Z",
                    required=True,
                ),
                "timezone": ParameterDef(
                    type="string",
                    description="The IANA timezone for the event, for example America/New_York",
                    required=True,
                ),
                "end_at": ParameterDef(
                    type="string",
                    description="The event end time as an ISO 8601 datetime",
                ),
                "description_md": ParameterDef(
                    type="string",
                    description="Markdown description for the event",
                ),
                "visibility": ParameterDef(
                    type="string",
                    description="Event visibility: public, members-only, or private",
                ),
                "slug": ParameterDef(
                    type="string",
                    description="Custom event URL slug",
                ),
                "meeting_url": ParameterDef(
                    type="string",
                    description="Online meeting URL for a virtual event",
                ),
                "cover_url": ParameterDef(
                    type="string",
                    description="Cover image URL uploaded to the Luma CDN",
                ),
                "max_capacity": ParameterDef(
                    type="integer",
                    description="Maximum number of registrations before the event is sold out",
                ),
                "can_register_for_multiple_tickets": ParameterDef(
                    type="boolean",
                    description="Whether guests can register for multiple tickets",
                ),
                "show_guest_list": ParameterDef(
                    type="boolean",
                    description="Whether approved guests can see who else is attending",
                ),
                "reminders_disabled": ParameterDef(
                    type="boolean",
                    description="Whether to disable default event reminders",
                ),
                "name_requirement": ParameterDef(
                    type="string",
                    description="How to collect guest names: full-name or first-last",
                ),
                "phone_number_requirement": ParameterDef(
                    type="string",
                    description="Phone number collection: optional or required",
                ),
                "tint_color": ParameterDef(
                    type="string",
                    description="A hex color like #bb2dc7 for the event theme",
                ),
                "coordinate_json": ParameterDef(
                    type="string",
                    description="JSON object with latitude and longitude for the event location",
                ),
                "geo_address_json": ParameterDef(
                    type="string",
                    description="JSON object with address details (type, place_id, description)",
                ),
                "registration_questions_json": ParameterDef(
                    type="string",
                    description="JSON array of registration question objects with label and required fields",
                ),
                "feedback_email_json": ParameterDef(
                    type="string",
                    description="JSON object with subject and message for the post-event feedback email",
                ),
            },
        ),
        ActionDefinition(
            name="get_event",
            description="Get admin details for a Luma event by event ID",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The Luma event ID (usually starts with evt-)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_events",
            description="List events managed by the connected Luma calendar",
            parameters={
                "after": ParameterDef(
                    type="string",
                    description="Return events starting after this ISO 8601 datetime",
                ),
                "before": ParameterDef(
                    type="string",
                    description="Return events starting before this ISO 8601 datetime",
                ),
                "pagination_cursor": ParameterDef(
                    type="string",
                    description="The next_cursor value from a previous list response",
                ),
                "pagination_limit": ParameterDef(
                    type="integer",
                    description="Number of items to request per page",
                    default=50,
                ),
                "status": ParameterDef(
                    type="string",
                    description="Calendar submission status: approved or pending",
                ),
                "sort_column": ParameterDef(
                    type="string",
                    description="Column to sort by (currently only start_at is supported)",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort order: asc, desc, asc nulls last, or desc nulls last",
                ),
            },
        ),
        ActionDefinition(
            name="get_guest",
            description="Get detailed information for a Luma event guest by ID or email",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The Luma event ID (usually starts with evt-)",
                    required=True,
                ),
                "guest_id": ParameterDef(
                    type="string",
                    description="Guest ID (gst-...), ticket key, guest key (g-...), or email address",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_guests",
            description="List guests registered for, invited to, or waitlisted for a Luma event",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The Luma event ID (usually starts with evt-)",
                    required=True,
                ),
                "approval_status": ParameterDef(
                    type="string",
                    description="Filter by status: approved, session, pending_approval, invited, declined, or waitlist",
                ),
                "pagination_cursor": ParameterDef(
                    type="string",
                    description="The next_cursor value from a previous list response",
                ),
                "pagination_limit": ParameterDef(
                    type="integer",
                    description="Number of items to request per page",
                    default=50,
                ),
                "sort_column": ParameterDef(
                    type="string",
                    description="Guest field to sort by: name, email, created_at, registered_at, or checked_in_at",
                ),
                "sort_direction": ParameterDef(
                    type="string",
                    description="Sort order: asc, desc, asc nulls last, or desc nulls last",
                ),
            },
        ),
        ActionDefinition(
            name="add_guests",
            description="Add guests to a Luma event with status Going",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The Luma event ID (usually starts with evt-)",
                    required=True,
                ),
                "guests_json": ParameterDef(
                    type="string",
                    description="JSON array of guests, each with at least an email field",
                    required=True,
                ),
                "ticket_json": ParameterDef(
                    type="string",
                    description="JSON object assigning one ticket type to each guest (mutually exclusive with tickets_json)",
                ),
                "tickets_json": ParameterDef(
                    type="string",
                    description="JSON array assigning multiple tickets to each guest (mutually exclusive with ticket_json)",
                ),
            },
        ),
        ActionDefinition(
            name="list_ticket_types",
            description="List ticket types for a Luma event",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The Luma event ID (usually starts with evt-)",
                    required=True,
                ),
                "include_hidden": ParameterDef(
                    type="boolean",
                    description="Whether to include hidden ticket types",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="send_invites",
            description="Send email invitations for a Luma event",
            parameters={
                "event_id": ParameterDef(
                    type="string",
                    description="The Luma event ID (usually starts with evt-)",
                    required=True,
                ),
                "guests_json": ParameterDef(
                    type="string",
                    description="JSON array of guests to invite, each with at least an email field",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Optional invite message (max 200 characters)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Luma API key",
            setup_instructions=[
                "Go to https://lu.ma and sign in to your account",
                "Navigate to your calendar settings or developer section",
                "Generate or copy your API key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="LUMA_API_KEY",
                    display_name="Luma API Key",
                    description="Your Luma API key",
                    required=True,
                    sensitive=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://docs.luma.com",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://public-api.luma.com/v1/calendar/list-events",
                method="GET",
                headers={"x-luma-api-key": "{api_key}"},
                params={"pagination_limit": "1"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["entries"],
                ),
                cost_level="free",
                description="Validates the API key by listing calendar events",
            ),
        ),
    ],
)
