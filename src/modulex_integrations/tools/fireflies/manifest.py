"""Fireflies integration manifest.

Declares the ten meeting-intelligence actions, their parameters, and the
API-key credential schema the modulex runtime uses to drive credential UI,
validation, and tool discovery.
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


_TRANSCRIPT_ID_PARAM = ParameterDef(
    type="string",
    description='The transcript ID (e.g. "abc123def456")',
    required=True,
)

_LANGUAGE_PARAM = ParameterDef(
    type="string",
    description='Transcription language code, e.g. "es", "de", "fr" (defaults to English)',
)

_SKIP_PARAM = ParameterDef(
    type="integer",
    description="Number of records to skip, for pagination",
)


manifest = IntegrationManifest(
    name="fireflies",
    display_name="Fireflies",
    description=(
        "Work with Fireflies.ai meeting recordings: browse and search transcripts, "
        "read a full transcript with its summary, action items and speaker "
        "analytics, upload audio for transcription, send the notetaker bot into a "
        "live meeting, clip and list soundbites, and look up team users and "
        "meeting contacts."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:fireflies",
    app_url="https://fireflies.ai",
    categories=["Productivity & Collaboration", "meeting", "note-taking"],
    actions=[
        ActionDefinition(
            name="list_transcripts",
            description=(
                "List meeting transcripts, optionally filtered by keyword, date range, "
                "host email, or participant email."
            ),
            parameters={
                "keyword": ParameterDef(
                    type="string",
                    description=(
                        'Search meeting titles and spoken words (e.g. "quarterly review")'
                    ),
                ),
                "from_date": ParameterDef(
                    type="string",
                    description=(
                        "Only meetings from this ISO 8601 timestamp onwards "
                        "(e.g. 2026-01-01T00:00:00Z)"
                    ),
                ),
                "to_date": ParameterDef(
                    type="string",
                    description=(
                        "Only meetings up to this ISO 8601 timestamp "
                        "(e.g. 2026-12-31T23:59:59Z)"
                    ),
                ),
                "host_email": ParameterDef(
                    type="string",
                    description="Filter by the meeting host's email address",
                ),
                "participants": ParameterDef(
                    type="array",
                    description=(
                        "Filter by participant email addresses (a list, or a "
                        "comma-separated string)"
                    ),
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of transcripts to return (max 50)",
                ),
                "skip": _SKIP_PARAM,
            },
        ),
        ActionDefinition(
            name="get_transcript",
            description=(
                "Get one transcript in full — every sentence with speaker attribution "
                "and timing, plus the AI summary, action items, and meeting analytics."
            ),
            parameters={"transcript_id": _TRANSCRIPT_ID_PARAM},
        ),
        ActionDefinition(
            name="get_user",
            description=(
                "Get a user's profile and usage. Returns the owner of the API key when "
                "no user ID is given."
            ),
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description=(
                        "User ID to retrieve; leave empty for the owner of the API key"
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_users",
            description=(
                "List the users in your team, with transcript counts, minutes consumed, "
                "and connected integrations."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="upload_audio",
            description=(
                "Submit a publicly reachable audio or video URL (mp3, mp4, wav, m4a, "
                "ogg) for transcription."
            ),
            parameters={
                "audio_url": ParameterDef(
                    type="string",
                    description=(
                        "Public https:// URL of the audio/video file to transcribe"
                    ),
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title for the resulting meeting/transcript",
                ),
                "webhook": ParameterDef(
                    type="string",
                    description=(
                        "Your own https:// endpoint that Fireflies POSTs the finished "
                        "transcript to. Leave unset unless you operate the receiving "
                        "endpoint"
                    ),
                ),
                "language": _LANGUAGE_PARAM,
                "attendees": ParameterDef(
                    type="array",
                    description=(
                        "Attendees as a JSON array of objects with displayName, email, "
                        'and/or phoneNumber, e.g. [{"displayName": "Ada", '
                        '"email": "ada@example.com"}]'
                    ),
                ),
                "client_reference_id": ParameterDef(
                    type="string",
                    description="Custom reference ID echoed back on webhook events",
                ),
            },
        ),
        ActionDefinition(
            name="delete_transcript",
            description=(
                "Delete a transcript and return the details of the meeting that was "
                "removed. Deleting another team member's meeting requires admin rights."
            ),
            parameters={"transcript_id": _TRANSCRIPT_ID_PARAM},
        ),
        ActionDefinition(
            name="add_to_live_meeting",
            description=(
                "Send the notetaker bot into an ongoing Zoom, Google Meet, or Microsoft "
                "Teams meeting to record and transcribe it."
            ),
            parameters={
                "meeting_link": ParameterDef(
                    type="string",
                    description=(
                        "Meeting URL for Zoom, Google Meet, Microsoft Teams, etc."
                    ),
                    required=True,
                ),
                "title": ParameterDef(
                    type="string",
                    description="Title for the meeting (max 256 characters)",
                ),
                "meeting_password": ParameterDef(
                    type="string",
                    description="Meeting password if one is required (max 32 characters)",
                ),
                "duration": ParameterDef(
                    type="integer",
                    description=(
                        "How long the bot should stay, in minutes (15-120, default 60)"
                    ),
                ),
                "language": _LANGUAGE_PARAM,
            },
        ),
        ActionDefinition(
            name="create_bite",
            description=(
                "Clip a soundbite (highlight) from a time range of a transcript for "
                "sharing."
            ),
            parameters={
                "transcript_id": ParameterDef(
                    type="string",
                    description="ID of the transcript to clip the soundbite from",
                    required=True,
                ),
                "start_time": ParameterDef(
                    type="number",
                    description="Start of the soundbite, in seconds",
                    required=True,
                ),
                "end_time": ParameterDef(
                    type="number",
                    description="End of the soundbite, in seconds",
                    required=True,
                ),
                "name": ParameterDef(
                    type="string",
                    description="Name for the soundbite (max 256 characters)",
                ),
                "media_type": ParameterDef(
                    type="string",
                    description="Soundbite media type: 'video' or 'audio'",
                ),
                "summary": ParameterDef(
                    type="string",
                    description="Summary of the soundbite (max 500 characters)",
                ),
            },
        ),
        ActionDefinition(
            name="list_bites",
            description=(
                "List soundbites (highlights), optionally only those clipped from one "
                "transcript."
            ),
            parameters={
                "transcript_id": ParameterDef(
                    type="string",
                    description="Only return soundbites clipped from this transcript",
                ),
                "mine": ParameterDef(
                    type="boolean",
                    description="Only return soundbites owned by the API key owner",
                    default=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of soundbites to return (max 50)",
                ),
                "skip": _SKIP_PARAM,
            },
        ),
        ActionDefinition(
            name="list_contacts",
            description=(
                "List the people you have met with, with the date of the most recent "
                "meeting."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="API Key Authentication",
            description="Authenticate using your Fireflies API key",
            setup_instructions=[
                "Sign in at https://app.fireflies.ai",
                "Open Settings -> Integrations and find the Fireflies API section "
                "(https://app.fireflies.ai/integrations/custom/fireflies)",
                "Click 'Generate New API Key' and copy the key",
                "Paste the API key below",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="FIREFLIES_API_KEY",
                    display_name="Fireflies API Key",
                    description="Your Fireflies API key from Settings -> Integrations",
                    required=True,
                    sensitive=True,
                    about_url="https://app.fireflies.ai/integrations/custom/fireflies",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://api.fireflies.ai/graphql",
                method="POST",
                headers={
                    "Authorization": "Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                body={"query": "query TestCredential { user { user_id } }"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data.user.user_id"],
                ),
                cost_level="free",
                description=(
                    "Validates the API key by reading the profile of its owner"
                ),
            ),
        ),
    ],
)
