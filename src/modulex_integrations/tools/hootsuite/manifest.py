"""Hootsuite integration manifest."""
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
    name="hootsuite",
    display_name="Hootsuite",
    description="Social media management platform for scheduling posts and managing profiles",
    version="1.0.0",
    author="ModuleX",
    logo="logos:hootsuite-icon",
    app_url="https://hootsuite.com",
    categories=["Social Media", "Marketing"],
    actions=[
        ActionDefinition(
            name="create_media_upload_job",
            description="Creates a new media upload job on Hootsuite by uploading a file from a public URL",
            parameters={
                "size_bytes": ParameterDef(
                    type="integer",
                    description="The size of the file in bytes",
                    required=True,
                ),
                "mime_type": ParameterDef(
                    type="string",
                    description="The MIME type of the file (e.g. image/png, image/jpeg, video/mp4)",
                    required=True,
                ),
                "file_url": ParameterDef(
                    type="string",
                    description="A publicly-accessible URL to the file to upload",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_media_upload_status",
            description="Gets the status of a media upload job on Hootsuite",
            parameters={
                "file_id": ParameterDef(
                    type="string",
                    description="The ID of the media file to check status for",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_social_profiles",
            description="Retrieves a list of social profiles for the authenticated Hootsuite account",
            parameters={},
        ),
        ActionDefinition(
            name="schedule_message",
            description="Schedules a message to be published on one or more social profiles",
            parameters={
                "text": ParameterDef(
                    type="string",
                    description="The message text to publish",
                    required=True,
                ),
                "social_profile_ids": ParameterDef(
                    type="array",
                    description="Array of social profile ID strings to post to (use list_social_profiles to discover IDs)",
                    required=True,
                ),
                "scheduled_send_time": ParameterDef(
                    type="string",
                    description="ISO-8601 UTC time to send the message (must end with 'Z'). If omitted, sends immediately.",
                ),
                "media_urls": ParameterDef(
                    type="array",
                    description="Array of ow.ly media URLs to attach to the message",
                ),
                "media": ParameterDef(
                    type="array",
                    description="Array of media IDs from create_media_upload_job to attach",
                ),
                "tags": ParameterDef(
                    type="array",
                    description="Array of Hootsuite message tags to apply (case sensitive)",
                ),
                "webhook_urls": ParameterDef(
                    type="array",
                    description="Array of webhook URLs to call when message state changes",
                ),
                "targeting": ParameterDef(
                    type="object",
                    description="Targeting object for Facebook Page and LinkedIn Company posts. See Hootsuite API docs for structure.",
                ),
                "privacy": ParameterDef(
                    type="object",
                    description="Privacy settings object with optional facebook.visibility and linkedIn.visibility arrays",
                ),
                "latitude": ParameterDef(
                    type="number",
                    description="Latitude in decimal degrees (-90 to 90)",
                ),
                "longitude": ParameterDef(
                    type="number",
                    description="Longitude in decimal degrees (-180 to 180)",
                ),
                "email_notification": ParameterDef(
                    type="boolean",
                    description="Whether to send email notification when the message is published",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Hootsuite OAuth (recommended)",
            setup_environment_variables=[
                EnvVar(
                    name="HOOTSUITE_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Hootsuite OAuth App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    about_url="https://developer.hootsuite.com/docs/getting-started",
                ),
                EnvVar(
                    name="HOOTSUITE_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Hootsuite OAuth App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://developer.hootsuite.com/docs/getting-started",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://platform.hootsuite.com/oauth2/auth",
                token_url="https://platform.hootsuite.com/oauth2/token",
                scopes=["offline"],
            ),
            test_endpoint=TestEndpoint(
                url="https://platform.hootsuite.com/v1/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["data"],
                ),
                cost_level="free",
                description="Validates OAuth token by fetching current user info",
            ),
        ),
    ],
)
