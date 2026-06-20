"""Grain integration manifest."""
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
    name="grain",
    display_name="Grain",
    description=(
        "Access Grain meeting recordings, transcripts, highlights, and "
        "AI-generated summaries. List and retrieve recordings with flexible "
        "filters, fetch full transcripts, browse teams, meeting types, and "
        "views, and manage webhook subscriptions for recording events."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:grain-themed",
    app_url="https://grain.com",
    categories=["Productivity & Collaboration", "meeting", "note-taking"],
    actions=[
        ActionDefinition(
            name="list_recordings",
            description="List recordings from Grain with optional filters and pagination",
            parameters={
                "cursor": ParameterDef(
                    type="string",
                    description=(
                        "Pagination cursor for next page (returned from previous response)"
                    ),
                ),
                "before_datetime": ParameterDef(
                    type="string",
                    description=(
                        "Only recordings before this ISO8601 timestamp "
                        '(e.g., "2024-01-15T00:00:00Z")'
                    ),
                ),
                "after_datetime": ParameterDef(
                    type="string",
                    description=(
                        "Only recordings after this ISO8601 timestamp "
                        '(e.g., "2024-01-01T00:00:00Z")'
                    ),
                ),
                "participant_scope": ParameterDef(
                    type="string",
                    description='Filter: "internal" or "external"',
                ),
                "title_search": ParameterDef(
                    type="string",
                    description=(
                        'Search term to filter by recording title (e.g., "weekly standup")'
                    ),
                ),
                "team_id": ParameterDef(
                    type="string",
                    description="Filter by team UUID",
                ),
                "meeting_type_id": ParameterDef(
                    type="string",
                    description="Filter by meeting type UUID",
                ),
                "include_highlights": ParameterDef(
                    type="boolean",
                    description="Include highlights/clips in response",
                    default=False,
                ),
                "include_participants": ParameterDef(
                    type="boolean",
                    description="Include participant list in response",
                    default=False,
                ),
                "include_ai_summary": ParameterDef(
                    type="boolean",
                    description="Include AI-generated summary",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_recording",
            description="Get details of a single recording by ID",
            parameters={
                "recording_id": ParameterDef(
                    type="string",
                    description="The recording UUID",
                    required=True,
                ),
                "include_highlights": ParameterDef(
                    type="boolean",
                    description="Include highlights/clips",
                    default=False,
                ),
                "include_participants": ParameterDef(
                    type="boolean",
                    description="Include participant list",
                    default=False,
                ),
                "include_ai_summary": ParameterDef(
                    type="boolean",
                    description="Include AI summary",
                    default=False,
                ),
                "include_calendar_event": ParameterDef(
                    type="boolean",
                    description="Include calendar event data",
                    default=False,
                ),
                "include_hubspot": ParameterDef(
                    type="boolean",
                    description="Include HubSpot associations",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_transcript",
            description="Get the full transcript of a recording",
            parameters={
                "recording_id": ParameterDef(
                    type="string",
                    description="The recording UUID",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_views",
            description="List available Grain views for webhook subscriptions",
            parameters={
                "type_filter": ParameterDef(
                    type="string",
                    description=(
                        "Optional view type filter: recordings, highlights, or stories"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_teams",
            description="List all teams in the workspace",
            parameters={},
        ),
        ActionDefinition(
            name="list_meeting_types",
            description="List all meeting types in the workspace",
            parameters={},
        ),
        ActionDefinition(
            name="create_hook",
            description="Create a webhook to receive recording events",
            parameters={
                "hook_url": ParameterDef(
                    type="string",
                    description=(
                        'Webhook endpoint URL (e.g., "https://example.com/webhooks/grain")'
                    ),
                    required=True,
                ),
                "view_id": ParameterDef(
                    type="string",
                    description="Grain view ID for the webhook subscription",
                    required=True,
                ),
                "actions": ParameterDef(
                    type="array",
                    description=(
                        "Optional list of actions to subscribe to: added, updated, removed"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_hooks",
            description="List all webhooks for the account",
            parameters={},
        ),
        ActionDefinition(
            name="delete_hook",
            description="Delete a webhook by ID",
            parameters={
                "hook_id": ParameterDef(
                    type="string",
                    description="The hook UUID to delete",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Grain personal access token",
            setup_instructions=[
                "Log in to your Grain account at https://grain.com",
                "Open Settings and navigate to the API / Integrations section",
                "Create a Personal Access Token (developer access may require approval)",
                "Paste the access token below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GRAIN_API_KEY",
                    display_name="Grain API Key",
                    description="Your Grain personal access token",
                    required=True,
                    sensitive=True,
                    about_url="https://developers.grain.com/",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.grain.com/_/public-api/v2/teams",
                method="POST",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {api_key}",
                    "Public-Api-Version": "2025-10-31",
                },
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates the API key by listing workspace teams",
            ),
        ),
    ],
)
