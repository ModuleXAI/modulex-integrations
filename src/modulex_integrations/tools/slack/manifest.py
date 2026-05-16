"""Slack integration manifest.

Direct pydantic translation of the legacy
``modulex/py/app/integrations/tools/slack_integration.json``.

The legacy JSON carries informational fields not present in our
schema (``docs_url``, ``required_permissions``, ``features``,
``rate_limits``, ``metadata``, per-action ``display_name``). Those
are dropped during migration — they were never read by the runtime,
only by the legacy admin UI.
"""
from __future__ import annotations

from modulex_integrations.schema import (
    ActionDefinition,
    BearerTokenAuthSchema,
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
    name="slack",
    display_name="Slack",
    description=(
        "Team communication and collaboration platform for messaging, "
        "channels, and workspace management"
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:slack-icon",
    app_url="https://slack.com",
    categories=["Communication & Collaboration", "collaboration", "messaging"],
    actions=[
        ActionDefinition(
            name="list_channels",
            description="List public channels in the Slack workspace with pagination",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description="Team/workspace ID to filter channels",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of channels to return (max 200)",
                    default=100,
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor for next page of results",
                ),
            },
        ),
        ActionDefinition(
            name="post_message",
            description="Post a new message to a Slack channel",
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="The ID of the channel to post to",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The message text to post",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="reply_to_thread",
            description="Reply to a specific message thread in Slack",
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="The ID of the channel containing the thread",
                    required=True,
                ),
                "thread_ts": ParameterDef(
                    type="string",
                    description=(
                        "The timestamp of the parent message "
                        "(format: '1234567890.123456')"
                    ),
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="The reply text",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="add_reaction",
            description="Add a reaction emoji to a message",
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="The ID of the channel containing the message",
                    required=True,
                ),
                "timestamp": ParameterDef(
                    type="string",
                    description="The timestamp of the message to react to",
                    required=True,
                ),
                "reaction": ParameterDef(
                    type="string",
                    description="The name of the emoji reaction (without colons)",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_channel_history",
            description="Get recent messages from a Slack channel",
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="The ID of the channel",
                    required=True,
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of messages to retrieve",
                    default=10,
                ),
            },
        ),
        ActionDefinition(
            name="get_thread_replies",
            description="Get all replies in a message thread",
            parameters={
                "channel_id": ParameterDef(
                    type="string",
                    description="The ID of the channel containing the thread",
                    required=True,
                ),
                "thread_ts": ParameterDef(
                    type="string",
                    description=(
                        "The timestamp of the parent message "
                        "(format: '1234567890.123456')"
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_users",
            description=(
                "Get a list of all users in the Slack workspace with their basic "
                "profile information"
            ),
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description="Team/workspace ID",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Maximum number of users to return (max 200)",
                    default=100,
                ),
                "cursor": ParameterDef(
                    type="string",
                    description="Pagination cursor for next page of results",
                ),
            },
        ),
        ActionDefinition(
            name="get_user_profile",
            description="Get detailed profile information for a specific user",
            parameters={
                "user_id": ParameterDef(
                    type="string",
                    description="The ID of the user",
                    required=True,
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description="Connect using Slack OAuth (recommended for most use cases)",
            setup_instructions=[
                "Create a Slack App at https://api.slack.com/apps",
                "Go to 'OAuth & Permissions'",
                "Add required scopes (see below)",
                "Install app to workspace",
                "Copy the Bot User OAuth Token",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SLACK_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description="Slack App Client ID",
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="1234567890.1234567890",
                    about_url="https://api.slack.com/apps",
                ),
                EnvVar(
                    name="SLACK_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description="Slack App Client Secret",
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    sample_format="x" * 32,
                    about_url="https://api.slack.com/apps",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://slack.com/oauth/v2/authorize",
                token_url="https://slack.com/api/oauth.v2.access",
                scopes=[
                    "channels:read",
                    "channels:history",
                    "chat:write",
                    "reactions:write",
                    "users:read",
                    "users.profile:read",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://slack.com/api/auth.test",
                method="POST",
                headers={
                    "Authorization": "Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["ok", "user_id", "team_id"],
                ),
                cost_level="free",
                description=(
                    "Validates Slack token using auth.test (no cost, Tier 4 rate limit)"
                ),
            ),
        ),
        BearerTokenAuthSchema(
            display_name="Bot Token",
            description="Use your Slack Bot User OAuth Token (xoxb-...)",
            setup_instructions=[
                "Go to https://api.slack.com/apps and create or select your app",
                "Navigate to 'OAuth & Permissions' in the sidebar",
                "Add the required Bot Token Scopes",
                "Install the app to your workspace",
                "Copy the 'Bot User OAuth Token' (starts with xoxb-)",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="SLACK_BOT_TOKEN",
                    display_name="Bot User OAuth Token",
                    description="Your Slack Bot User OAuth Token (starts with xoxb-)",
                    required=True,
                    sensitive=True,
                    sample_format="xoxb-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx",
                    about_url="https://api.slack.com/apps",
                ),
            ],
            test_endpoint=TestEndpoint(
                url="https://slack.com/api/auth.test",
                method="POST",
                headers={
                    "Authorization": "Bearer {token}",
                    "Content-Type": "application/json",
                },
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["ok", "user_id", "team_id"],
                ),
                cost_level="free",
                description="Validates Bot Token by testing authentication (no API cost)",
            ),
        ),
    ],
)
