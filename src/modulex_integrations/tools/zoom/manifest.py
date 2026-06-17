"""Zoom integration manifest."""
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
    name="zoom",
    display_name="Zoom",
    description="Video conferencing, meetings, webinars, and team chat platform",
    version="1.0.0",
    author="ModuleX",
    logo="logos:zoom-icon",
    app_url="https://zoom.us",
    categories=["Communication", "Video Conferencing", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_meeting",
            description="Create a meeting for the authenticated user. A maximum of 100 meetings can be created per day.",
            parameters={
                "topic": ParameterDef(
                    type="string",
                    description="Meeting topic",
                ),
                "type": ParameterDef(
                    type="integer",
                    description="Meeting type: 1 - Instant, 2 - Scheduled, 3 - Recurring no fixed time, 8 - Recurring fixed time",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Meeting start time in yyyy-MM-ddTHH:mm:ssZ (GMT) or yyyy-MM-ddTHH:mm:ss (with timezone field). Used for scheduled/recurring meetings.",
                ),
                "duration": ParameterDef(
                    type="integer",
                    description="Meeting duration in minutes. Used for scheduled meetings only.",
                ),
                "timezone": ParameterDef(
                    type="string",
                    description="Time zone for start_time, e.g. America/Los_Angeles. For scheduled meetings only.",
                ),
                "password": ParameterDef(
                    type="string",
                    description="Password to join the meeting. May contain [a-z A-Z 0-9 @ - _ *], max 10 characters.",
                ),
                "agenda": ParameterDef(
                    type="string",
                    description="Meeting description/agenda",
                ),
            },
        ),
        ActionDefinition(
            name="list_meetings",
            description="List meetings for a user",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The user ID or email address of the user. Use 'me' for the current user.",
                    required=True,
                ),
                "type": ParameterDef(
                    type="string",
                    description="Type of meetings to list: scheduled, live, upcoming, previous_meetings. Defaults to scheduled.",
                ),
            },
        ),
        ActionDefinition(
            name="get_meeting_details",
            description="Retrieve the details of a meeting",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The meeting ID",
                    required=True,
                ),
                "occurrence_id": ParameterDef(
                    type="string",
                    description="Meeting occurrence ID for recurring meetings",
                ),
            },
        ),
        ActionDefinition(
            name="update_meeting",
            description="Update an existing Zoom meeting's topic, time, or other settings",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The Zoom meeting ID to update",
                    required=True,
                ),
                "topic": ParameterDef(
                    type="string",
                    description="Meeting topic",
                ),
                "type": ParameterDef(
                    type="integer",
                    description="Meeting type: 1 - Instant, 2 - Scheduled, 3 - Recurring no fixed time, 8 - Recurring fixed time",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Meeting start time",
                ),
                "duration": ParameterDef(
                    type="integer",
                    description="Meeting duration in minutes",
                ),
                "timezone": ParameterDef(
                    type="string",
                    description="Time zone for start_time",
                ),
                "password": ParameterDef(
                    type="string",
                    description="Password to join the meeting, max 10 characters",
                ),
                "agenda": ParameterDef(
                    type="string",
                    description="Meeting description/agenda",
                ),
            },
        ),
        ActionDefinition(
            name="delete_meeting",
            description="Delete a meeting",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The ID of the meeting to delete",
                    required=True,
                ),
                "occurrence_id": ParameterDef(
                    type="string",
                    description="If provided, only that occurrence will be deleted. Otherwise the entire meeting series is deleted.",
                ),
                "schedule_for_reminder": ParameterDef(
                    type="boolean",
                    description="If true, notify host and alternative host about the meeting cancellation via email",
                ),
                "cancel_meeting_reminder": ParameterDef(
                    type="boolean",
                    description="If true, notify registrants about the meeting cancellation via email",
                ),
            },
        ),
        ActionDefinition(
            name="get_current_user",
            description="Return the authenticated Zoom user's ID, name, email, account ID, and timezone",
            parameters={},
        ),
        ActionDefinition(
            name="send_chat_message",
            description="Send a chat message on Zoom to an individual contact or a channel",
            parameters={
                "message": ParameterDef(
                    type="string",
                    description="The message to be sent",
                    required=True,
                ),
                "to_contact": ParameterDef(
                    type="string",
                    description="The email address of the contact to send the message to",
                ),
                "to_channel": ParameterDef(
                    type="string",
                    description="The channel ID to send the message to",
                ),
            },
        ),
        ActionDefinition(
            name="list_channels",
            description="List the authenticated user's chat channels",
            parameters={
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of records per page",
                ),
                "next_page_token": ParameterDef(
                    type="string",
                    description="Next page token for pagination. Expires after 15 minutes.",
                ),
            },
        ),
        ActionDefinition(
            name="add_meeting_registrant",
            description="Register a participant for a meeting",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The meeting ID",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="A valid email address of the registrant",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Registrant's first name",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Registrant's last name",
                    required=True,
                ),
                "occurrence_ids": ParameterDef(
                    type="string",
                    description="Occurrence IDs, multiple values separated by comma",
                ),
            },
        ),
        ActionDefinition(
            name="get_meeting_recordings",
            description="Get the recordings of a meeting",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The meeting ID to get recordings for",
                    required=True,
                ),
                "download_access_token": ParameterDef(
                    type="boolean",
                    description="Whether to include a download access token in the response",
                ),
            },
        ),
        ActionDefinition(
            name="get_meeting_transcript",
            description="Get the transcript of a past meeting as speaker-attributed plain text",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The ID of a past meeting with cloud recording and audio transcription enabled",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_meeting_summary",
            description="Retrieve the AI-generated summary of a meeting or webinar",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The meeting ID or meeting UUID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_all_recordings",
            description="List all cloud recordings for a user",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The user ID or email. Use 'me' for the current user.",
                    default="me",
                ),
                "from_date": ParameterDef(
                    type="string",
                    description="Start date in yyyy-MM-dd format. Maximum date range is one month.",
                ),
                "to_date": ParameterDef(
                    type="string",
                    description="End date in yyyy-MM-dd format",
                ),
                "trash": ParameterDef(
                    type="boolean",
                    description="If true, list recordings from trash",
                ),
            },
        ),
        ActionDefinition(
            name="list_call_recordings",
            description="Get your account's Zoom Phone call recordings",
            parameters={
                "start_date": ParameterDef(
                    type="string",
                    description="Start date in yyyy-MM-dd or yyyy-MM-ddTHH:mm:ssZ format",
                ),
                "end_date": ParameterDef(
                    type="string",
                    description="End date in yyyy-MM-dd or yyyy-MM-ddTHH:mm:ssZ format. Max 30-day range.",
                ),
            },
        ),
        ActionDefinition(
            name="list_user_call_logs",
            description="Get a user's Zoom Phone call logs",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The user ID or email address of the user",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_past_meeting_participants",
            description="Retrieve participants from a past meeting",
            parameters={
                "meeting_id": ParameterDef(
                    type="string",
                    description="The meeting ID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_user",
            description="Create a new user in your Zoom account",
            parameters={
                "action": ParameterDef(
                    type="string",
                    description="How to create the user: create, autoCreate, custCreate, ssoCreate",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="User's email address",
                    required=True,
                ),
                "type": ParameterDef(
                    type="integer",
                    description="User type: 1 - Basic, 2 - Licensed, 3 - On-prem",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="User's first name",
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="User's last name",
                ),
            },
        ),
        ActionDefinition(
            name="delete_user",
            description="Disassociate or permanently delete a user from the account",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The user ID or email address",
                    required=True,
                ),
                "action": ParameterDef(
                    type="string",
                    description="Delete action: disassociate or delete",
                ),
                "transfer_email": ParameterDef(
                    type="string",
                    description="Email to transfer resources to",
                ),
                "transfer_meeting": ParameterDef(
                    type="boolean",
                    description="Transfer meetings to the transfer_email user",
                ),
                "transfer_webinar": ParameterDef(
                    type="boolean",
                    description="Transfer webinars to the transfer_email user",
                ),
                "transfer_recording": ParameterDef(
                    type="boolean",
                    description="Transfer recordings to the transfer_email user",
                ),
            },
        ),
        ActionDefinition(
            name="get_webinar_details",
            description="Get details of a scheduled webinar",
            parameters={
                "webinar_id": ParameterDef(
                    type="string",
                    description="The webinar ID",
                    required=True,
                ),
                "occurrence_id": ParameterDef(
                    type="string",
                    description="Unique identifier for an occurrence of a recurring webinar",
                ),
            },
        ),
        ActionDefinition(
            name="update_webinar",
            description="Update a webinar's topic, start time, or other settings",
            parameters={
                "webinar_id": ParameterDef(
                    type="string",
                    description="The Zoom webinar ID to update",
                    required=True,
                ),
                "topic": ParameterDef(
                    type="string",
                    description="Webinar topic",
                ),
                "type": ParameterDef(
                    type="integer",
                    description="Webinar type: 5 - Webinar, 6 - Recurring no fixed time, 9 - Recurring fixed time",
                ),
                "start_time": ParameterDef(
                    type="string",
                    description="Webinar start time",
                ),
                "duration": ParameterDef(
                    type="integer",
                    description="Webinar duration in minutes",
                ),
                "timezone": ParameterDef(
                    type="string",
                    description="Time zone for start_time",
                ),
                "password": ParameterDef(
                    type="string",
                    description="Password to join the webinar, max 10 characters",
                ),
                "agenda": ParameterDef(
                    type="string",
                    description="Webinar description/agenda",
                ),
            },
        ),
        ActionDefinition(
            name="add_webinar_registrant",
            description="Register a participant for a webinar",
            parameters={
                "webinar_id": ParameterDef(
                    type="string",
                    description="The webinar ID",
                    required=True,
                ),
                "email": ParameterDef(
                    type="string",
                    description="A valid email address of the registrant",
                    required=True,
                ),
                "first_name": ParameterDef(
                    type="string",
                    description="Registrant's first name",
                    required=True,
                ),
                "last_name": ParameterDef(
                    type="string",
                    description="Registrant's last name",
                    required=True,
                ),
                "occurrence_ids": ParameterDef(
                    type="string",
                    description="Occurrence IDs, multiple values separated by comma",
                ),
            },
        ),
        ActionDefinition(
            name="list_webinar_participants_report",
            description="Retrieve detailed report on each webinar attendee. Reports available for the last 6 months.",
            parameters={
                "webinar_id": ParameterDef(
                    type="string",
                    description="The webinar ID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_past_webinar_qa",
            description="List Q&A from a past webinar",
            parameters={
                "webinar_id": ParameterDef(
                    type="string",
                    description="The Zoom webinar ID",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Zoom OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="ZOOM_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Zoom OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://marketplace.zoom.us/develop/create",
                ),
                EnvVar(
                    name="ZOOM_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Zoom OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://marketplace.zoom.us/develop/create",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://zoom.us/oauth/authorize",
                token_url="https://zoom.us/oauth/token",
                scopes=[
                    "meeting:write:admin",
                    "meeting:read:admin",
                    "recording:read:admin",
                    "chat_message:write",
                    "chat_channel:read",
                    "user:read:admin",
                    "user:write:admin",
                    "phone:read:admin",
                    "webinar:read:admin",
                    "webinar:write:admin",
                    "report:read:admin",
                ],
                token_auth_method="basic",
            ),
            test_endpoint=TestEndpoint(
                url="https://api.zoom.us/v2/users/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching authenticated user info",
            ),
        ),
    ],
)
