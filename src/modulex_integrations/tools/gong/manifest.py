"""Gong integration manifest."""
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
    name="gong",
    display_name="Gong",
    description="Revenue intelligence platform for recording, transcribing, and analyzing sales conversations",
    version="1.0.0",
    author="ModuleX",
    logo="modulex:gong",
    app_url="https://www.gong.io",
    categories=["Sales", "Revenue Intelligence", "Conversation Analytics"],
    actions=[
        ActionDefinition(
            name="add_new_call",
            description="Add a new call to Gong",
            parameters={
                "client_unique_id": ParameterDef(
                    type="string",
                    description="A call's unique identifier in the PBX or recording system. Used to prevent duplicate uploads.",
                    required=True,
                ),
                "actual_start": ParameterDef(
                    type="string",
                    description="The actual date and time when the call started in ISO-8601 format (e.g., 2018-02-18T02:30:00-07:00 or 2018-02-18T08:00:00Z).",
                    required=True,
                ),
                "direction": ParameterDef(
                    type="string",
                    description="Whether the call is Inbound, Outbound, Conference, or Unknown.",
                    required=True,
                ),
                "primary_user": ParameterDef(
                    type="string",
                    description="The Gong internal user ID of the team member who hosted the call.",
                    required=True,
                ),
                "parties": ParameterDef(
                    type="array",
                    description="A list of the call's participants as JSON objects. Each party can have: phoneNumber, emailAddress, name, mediaChannelId.",
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="The title of the call, available for indexing and search.",
                ),
                "purpose": ParameterDef(
                    type="string",
                    description="The purpose of the call. Free text up to 255 characters.",
                ),
                "scheduled_start": ParameterDef(
                    type="string",
                    description="The date and time the call was scheduled to begin in ISO-8601 format.",
                ),
                "scheduled_end": ParameterDef(
                    type="string",
                    description="The date and time the call was scheduled to end in ISO-8601 format.",
                ),
                "duration": ParameterDef(
                    type="integer",
                    description="The actual call duration in seconds.",
                ),
                "disposition": ParameterDef(
                    type="string",
                    description="The disposition of the call. Free text up to 255 characters.",
                ),
                "meeting_url": ParameterDef(
                    type="string",
                    description="The URL of the conference call by which users join the meeting.",
                ),
                "call_provider_code": ParameterDef(
                    type="string",
                    description="Code identifying the conferencing/telephony system: zoom, clearslide, gotomeeting, ringcentral, outreach, insidesales.",
                ),
                "download_media_url": ParameterDef(
                    type="string",
                    description="The URL from which Gong can download the media file. Must be unique, max 1.5GB.",
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="Optional workspace identifier for call placement.",
                ),
                "language_code": ParameterDef(
                    type="string",
                    description="Language code for transcription (e.g., en-US, fr-FR). Optional; Gong auto-detects if not set.",
                ),
            },
        ),
        ActionDefinition(
            name="get_extensive_data",
            description="List detailed call data with content selectors for topics, trackers, transcripts, and more",
            parameters={
                "from_date_time": ParameterDef(
                    type="string",
                    description="Date and time (ISO-8601) from which to list recorded calls.",
                ),
                "to_date_time": ParameterDef(
                    type="string",
                    description="Date and time (ISO-8601) until which to list recorded calls.",
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The ID of the workspace to filter by.",
                ),
                "call_ids": ParameterDef(
                    type="array",
                    description="List of call ID strings to filter. If not supplied, returns all calls in date range.",
                ),
                "primary_user_ids": ParameterDef(
                    type="array",
                    description="List of user ID strings. If supplied, returns only calls hosted by these users.",
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description="Maximum number of results to return.",
                    default=600,
                ),
                "context": ParameterDef(
                    type="string",
                    description="Context level: None, Basic (add links), or Extended (include link data).",
                    default="None",
                ),
                "context_timing": ParameterDef(
                    type="array",
                    description="Timing for context data: 'Now' or 'TimeOfCall' or both. Only valid when context is Extended.",
                ),
                "include_parties": ParameterDef(
                    type="boolean",
                    description="Whether to include parties in the response.",
                    default=False,
                ),
                "exposed_fields_content": ParameterDef(
                    type="object",
                    description="Fields to include for content: structure, topics, trackers, trackerOccurrences, pointsOfInterest, brief, outline, highlights, callOutcome, keyPoints (boolean values).",
                ),
                "exposed_fields_interaction": ParameterDef(
                    type="object",
                    description="Fields to include for interaction: speakers, video, personInteractionStats, questions (boolean values).",
                ),
                "include_public_comments": ParameterDef(
                    type="boolean",
                    description="Whether to include public comments in the response.",
                    default=False,
                ),
                "include_media": ParameterDef(
                    type="boolean",
                    description="Whether to include media in the response.",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_calls",
            description="List calls with optional date range filtering",
            parameters={
                "from_date_time": ParameterDef(
                    type="string",
                    description="Date and time (ISO-8601) from which to list recorded calls.",
                ),
                "to_date_time": ParameterDef(
                    type="string",
                    description="Date and time (ISO-8601) until which to list recorded calls.",
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor returned by a previous call.",
                ),
            },
        ),
        ActionDefinition(
            name="list_workspace_id_options",
            description="Retrieve available workspace IDs and names",
            parameters={},
        ),
        ActionDefinition(
            name="retrieve_transcripts_of_calls",
            description="Retrieve transcripts of calls with optional date range and call ID filtering",
            parameters={
                "from_date_time": ParameterDef(
                    type="string",
                    description="Date and time (ISO-8601) from which to filter calls.",
                ),
                "to_date_time": ParameterDef(
                    type="string",
                    description="Date and time (ISO-8601) until which to filter calls.",
                ),
                "workspace_id": ParameterDef(
                    type="string",
                    description="The ID of the workspace to filter by.",
                ),
                "call_ids": ParameterDef(
                    type="array",
                    description="List of call ID strings to retrieve transcripts for.",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Gong OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="GONG_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Gong OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://app.gong.io/company/api",
                ),
                EnvVar(
                    name="GONG_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Gong OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 40,
                    about_url="https://app.gong.io/company/api",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://app.gong.io/oauth2/authorize",
                token_url="https://app.gong.io/oauth2/generate-customer-token",
                scopes=[
                    "api:calls:read:basic",
                    "api:calls:read:extensive",
                    "api:calls:create",
                    "api:workspaces:read",
                    "api:calls:read:transcript",
                ],
            ),
            test_endpoint=TestEndpoint(
                url="https://us-66463.api.gong.io/v2/calls",
                method="GET",
                headers={
                    "Authorization": "Bearer {access_token}",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["requestId"],
                ),
                cost_level="free",
                description="Validates OAuth token by listing calls",
            ),
        ),
    ],
)
