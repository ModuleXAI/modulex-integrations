"""Granola integration manifest.

Declares the three meeting-notes actions, their parameters, and the
API-key credential schema the modulex runtime uses to drive credential
UI, validation, and tool discovery.
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


manifest = IntegrationManifest(
    name="granola",
    display_name="Granola",
    description=(
        "Retrieve meeting notes, summaries, attendees, calendar details, and "
        "transcripts from Granola."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:granola",
    app_url="https://granola.ai",
    categories=["Productivity & Collaboration", "meeting", "note-taking"],
    actions=[
        ActionDefinition(
            name="list_notes",
            description=(
                "Lists meeting notes from Granola with optional date filters and "
                "pagination."
            ),
            parameters={
                "created_before": ParameterDef(
                    type="string",
                    description="Return notes created before this date (ISO 8601)",
                ),
                "created_after": ParameterDef(
                    type="string",
                    description="Return notes created after this date (ISO 8601)",
                ),
                "updated_after": ParameterDef(
                    type="string",
                    description="Return notes updated after this date (ISO 8601)",
                ),
                "folder_id": ParameterDef(
                    type="string",
                    description=(
                        "Return notes in this folder and its child folders "
                        "(e.g., fol_4y6LduVdwSKC27)"
                    ),
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response",
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of notes per page (1-30, default 10)",
                ),
            },
        ),
        ActionDefinition(
            name="get_note",
            description=(
                "Retrieves a specific meeting note from Granola by ID, including "
                "summary, attendees, calendar event details, and optionally the "
                "transcript."
            ),
            parameters={
                "note_id": ParameterDef(
                    type="string",
                    description="The note ID (e.g., not_1d3tmYTlCICgjy)",
                    required=True,
                ),
                "include_transcript": ParameterDef(
                    type="boolean",
                    description="Whether to include the meeting transcript",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="list_folders",
            description="Lists folders from Granola, sorted alphabetically, with pagination.",
            parameters={
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor from a previous response",
                ),
                "page_size": ParameterDef(
                    type="integer",
                    description="Number of folders per page (1-30, default 10)",
                ),
            },
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Granola API key",
            setup_instructions=[
                "Open Granola and go to Settings (a Business plan is required)",
                "Navigate to the API / Developer section",
                "Create a new API key and copy it",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="GRANOLA_API_KEY",
                    display_name="Granola API Key",
                    description="Your Granola API key",
                    required=True,
                    sensitive=True,
                    sample_format="grn_xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://docs.granola.ai/introduction",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://public-api.granola.ai/v1/folders",
                method="GET",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                params={"page_size": "1"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["folders"],
                ),
                cost_level="free",
                description="Validates the API key by listing one folder",
            ),
        ),
    ],
)
