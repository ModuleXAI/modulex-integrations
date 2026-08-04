"""Fathom integration manifest.

Declares the six meeting-intelligence actions, their parameters, and
the API-key credential schema the modulex runtime uses to drive
credential UI, validation, and tool discovery.
"""
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


_CURSOR_PARAM = ParameterDef(
    type="string",
    description="Pagination cursor from a previous response",
)

_RECORDING_ID_PARAM = ParameterDef(
    type="string",
    description="The recording ID of the meeting (e.g., 123456789)",
    required=True,
)


manifest = IntegrationManifest(
    name="fathom",
    display_name="Fathom",
    description=(
        "Access Fathom AI Notetaker meeting data: list recorded meetings with "
        "summaries, transcripts, action items, highlights, and CRM matches, and "
        "browse meeting types, teams, and team members."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:fathom-themed",
    app_url="https://fathom.video",
    categories=["Productivity & Collaboration", "meeting", "note-taking"],
    actions=[
        ActionDefinition(
            name="list_meetings",
            description=(
                "List recent meetings recorded by the user or shared to their team. "
                "Supports date, recorder, team, meeting-type and invitee-domain "
                "filters, and can embed summaries, transcripts, action items, "
                "highlights, and CRM matches."
            ),
            parameters={
                "include_summary": ParameterDef(
                    type="boolean",
                    description="Include each meeting's summary in the response",
                    default=False,
                ),
                "include_transcript": ParameterDef(
                    type="boolean",
                    description="Include each meeting's full transcript in the response",
                    default=False,
                ),
                "include_action_items": ParameterDef(
                    type="boolean",
                    description="Include action items extracted from each meeting",
                    default=False,
                ),
                "include_crm_matches": ParameterDef(
                    type="boolean",
                    description=(
                        "Include CRM matches (only returns data from a linked CRM)"
                    ),
                    default=False,
                ),
                "include_highlights": ParameterDef(
                    type="boolean",
                    description="Include highlighted moments from each meeting",
                    default=False,
                ),
                "created_after": ParameterDef(
                    type="string",
                    description=(
                        "Only meetings created after this ISO 8601 timestamp "
                        "(e.g., 2025-01-01T00:00:00Z)"
                    ),
                ),
                "created_before": ParameterDef(
                    type="string",
                    description=(
                        "Only meetings created before this ISO 8601 timestamp "
                        "(e.g., 2025-12-31T23:59:59Z)"
                    ),
                ),
                "recorded_by": ParameterDef(
                    type="string",
                    description="Filter by the email address of the user who recorded",
                ),
                "teams": ParameterDef(
                    type="string",
                    description="Filter by team name",
                ),
                "meeting_type": ParameterDef(
                    type="string",
                    description=(
                        "Filter by meeting type name (see the list_meeting_types action)"
                    ),
                ),
                "calendar_invitees_domains": ParameterDef(
                    type="string",
                    description=(
                        "Filter by calendar invitee company domain (exact match)"
                    ),
                ),
                "calendar_invitees_domains_type": ParameterDef(
                    type="string",
                    description=(
                        "Invitee domain filter: 'all', 'only_internal', or "
                        "'one_or_more_external'"
                    ),
                ),
                "cursor": _CURSOR_PARAM,
            },
        ),
        ActionDefinition(
            name="list_meeting_types",
            description=(
                "List meeting types configured in your Fathom organization, "
                "including active and inactive ones."
            ),
            parameters={"cursor": _CURSOR_PARAM},
        ),
        ActionDefinition(
            name="get_summary",
            description=(
                "Get the markdown-formatted call summary for a specific meeting "
                "recording."
            ),
            parameters={"recording_id": _RECORDING_ID_PARAM},
        ),
        ActionDefinition(
            name="get_transcript",
            description=(
                "Get the full transcript for a specific meeting recording, with "
                "speaker attribution and timestamps."
            ),
            parameters={"recording_id": _RECORDING_ID_PARAM},
        ),
        ActionDefinition(
            name="list_team_members",
            description="List team members in your Fathom organization.",
            parameters={
                "team": ParameterDef(
                    type="string",
                    description="Team name to filter by",
                ),
                "cursor": _CURSOR_PARAM,
            },
        ),
        ActionDefinition(
            name="list_teams",
            description="List teams in your Fathom organization.",
            parameters={"cursor": _CURSOR_PARAM},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Fathom API key",
            setup_instructions=[
                "Sign in at https://fathom.video and open your User Settings",
                "Go to the 'API Access' section "
                "(https://fathom.video/customize#api-access-header)",
                "Generate a new API key and copy it",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FATHOM_API_KEY",
                    display_name="Fathom API Key",
                    description="Your Fathom API key from Settings -> API Access",
                    required=True,
                    sensitive=True,
                    about_url="https://fathom.video/customize#api-access-header",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.fathom.ai/external/v1/teams",
                method="GET",
                headers={
                    "X-Api-Key": "{api_key}",
                    "Accept": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["items"],
                ),
                cost_level="free",
                description="Validates the API key by listing the organization's teams",
            ),
        ),
    ],
)
