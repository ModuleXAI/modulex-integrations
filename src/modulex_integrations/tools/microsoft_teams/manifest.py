"""Microsoft Teams integration manifest."""
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
    name="microsoft_teams",
    display_name="Microsoft Teams",
    description=(
        "Create channels, send channel and chat messages, list "
        "teams/channels/chats/messages/shifts, search messages, and retrieve "
        "the current user via Microsoft Graph."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="modulex:microsoft_teams-themed",
    app_url="https://www.microsoft.com/microsoft-teams",
    categories=["Communication", "Productivity & Collaboration"],
    actions=[
        ActionDefinition(
            name="create_channel",
            description="Create a new channel in Microsoft Teams.",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Team. Obtain it via `list_teams`.",
                    required=True,
                ),
                "display_name": ParameterDef(
                    type="string",
                    description="Display name of the channel.",
                    required=True,
                ),
                "description": ParameterDef(
                    type="string",
                    description="Description of the channel.",
                ),
            },
        ),
        ActionDefinition(
            name="get_chat_message",
            description="Get a specific message from a chat.",
            parameters={
                "chat_id": ParameterDef(
                    type="string",
                    description="ID of the chat. Obtain it via `list_chats`.",
                    required=True,
                ),
                "message_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the message to retrieve. Obtain it via "
                        "`list_messages_in_chat`."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="get_current_user",
            description=(
                "Returns the authenticated Microsoft Teams user's ID, display name, "
                "email, and principal name via Microsoft Graph. Call this first when "
                "the user says 'my channels', 'my chats', or needs identity context."
            ),
            parameters={},
        ),
        ActionDefinition(
            name="list_channel_messages",
            description="Lists messages in a Microsoft Teams channel.",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Team.",
                    required=True,
                ),
                "channel_id": ParameterDef(
                    type="string",
                    description="ID of the channel within the team.",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description=(
                        "The maximum number of messages to return. Omit to fetch "
                        "all available pages."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_channels",
            description="Lists all channels in a Microsoft Team.",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Team.",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_chats",
            description="Lists all chat conversations for the authenticated user.",
            parameters={},
        ),
        ActionDefinition(
            name="list_messages_in_chat",
            description=(
                "Get the list of messages in a chat, ordered by createdDateTime "
                "descending."
            ),
            parameters={
                "chat_id": ParameterDef(
                    type="string",
                    description="ID of the chat.",
                    required=True,
                ),
                "max_results": ParameterDef(
                    type="integer",
                    description=(
                        "The maximum number of results to return. Omit to fetch "
                        "all available pages."
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="list_shifts",
            description="Get the list of shift instances for a team.",
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description=(
                        "ID of the Microsoft Team whose schedule is being queried."
                    ),
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="list_teams",
            description="Lists all teams the authenticated user has joined.",
            parameters={},
        ),
        ActionDefinition(
            name="search_messages",
            description=(
                "Search for email or chat messages via Microsoft Graph search. "
                "Valid entity_type values: `message` (email), `chatMessage` (Teams "
                "chat messages)."
            ),
            parameters={
                "entity_type": ParameterDef(
                    type="string",
                    description=(
                        "The type of entity to search for. Valid values: `message` "
                        "for email, `chatMessage` for Teams chat messages."
                    ),
                    required=True,
                ),
                "query_string": ParameterDef(
                    type="string",
                    description="The query string to search for.",
                    required=True,
                ),
                "from_": ParameterDef(
                    type="integer",
                    description="The index of the first result to return.",
                    default=0,
                ),
                "size": ParameterDef(
                    type="integer",
                    description="The number of results to return (max 25).",
                    default=25,
                ),
            },
        ),
        ActionDefinition(
            name="send_channel_message",
            description=(
                "Send a message to a team's channel. Optionally include inline "
                "images via `hosted_contents`."
            ),
            parameters={
                "team_id": ParameterDef(
                    type="string",
                    description="ID of the Microsoft Team.",
                    required=True,
                ),
                "channel_id": ParameterDef(
                    type="string",
                    description="ID of the channel within the team.",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Message to be sent.",
                    required=True,
                ),
                "content_type": ParameterDef(
                    type="string",
                    description=(
                        "Whether the message body is plain text or HTML. Valid "
                        "values: `text`, `html`."
                    ),
                    default="text",
                ),
                "hosted_contents": ParameterDef(
                    type="array",
                    description=(
                        "An array of JSON strings, each representing an inline "
                        "hosted image. Each item must be a JSON object with "
                        "`@microsoft.graph.temporaryId` (string), `contentBytes` "
                        "(base64-encoded image data), and `contentType` (MIME type, "
                        "e.g. `image/png`). Reference each image in HTML message "
                        'bodies using `<img src="../hostedContents/1/$value">`.'
                    ),
                ),
            },
        ),
        ActionDefinition(
            name="send_chat_message",
            description="Send a message to a team's chat.",
            parameters={
                "chat_id": ParameterDef(
                    type="string",
                    description="ID of the chat to post the message to.",
                    required=True,
                ),
                "message": ParameterDef(
                    type="string",
                    description="Message to be sent.",
                    required=True,
                ),
                "content_type": ParameterDef(
                    type="string",
                    description=(
                        "Whether the message body is plain text or HTML. Valid "
                        "values: `text`, `html`."
                    ),
                    default="text",
                ),
            },
        ),
    ],
    auth_schemas=[
        OAuth2AuthSchema(
            display_name="OAuth2 Authentication",
            description=(
                "Connect with your Microsoft work or school account using OAuth 2.0. "
                "Personal accounts are not supported by Microsoft Teams APIs."
            ),
            setup_instructions=[
                "Go to https://entra.microsoft.com (Microsoft Entra admin center) and open 'App registrations'",
                "Create a new registration (single-tenant or multi-tenant, as required by your deployment)",
                "Under Authentication, add the redirect URI: https://api.modulex.dev/credentials/oauth2/callback (type: Web)",
                "Under API permissions, add Microsoft Graph delegated permissions: User.Read, Team.ReadBasic.All, Channel.ReadBasic.All, ChannelMessage.Read.All, ChannelMessage.Send, Chat.ReadWrite, ChatMessage.Send, Schedule.Read.All, Mail.Read, and offline_access",
                "Grant admin consent for the tenant if your organization requires it",
                "Under Certificates & secrets, create a Client Secret and copy its Value",
                "Copy the Application (client) ID and the Client Secret Value into ModuleX",
            ],
            setup_environment_variables=[
                EnvVar(
                    name="MICROSOFT_TEAMS_OAUTH2_CLIENT_ID",
                    display_name="Client ID",
                    description=(
                        "Microsoft Entra Application (client) ID for the registered app."
                    ),
                    required=True,
                    sensitive=False,
                    only_for_custom=True,
                    sample_format="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                    about_url="https://entra.microsoft.com",
                ),
                EnvVar(
                    name="MICROSOFT_TEAMS_OAUTH2_CLIENT_SECRET",
                    display_name="Client Secret",
                    description=(
                        "Microsoft Entra Client Secret Value for the registered app."
                    ),
                    required=True,
                    sensitive=True,
                    only_for_custom=True,
                    about_url="https://entra.microsoft.com",
                ),
            ],
            oauth_config=OAuthConfig(
                auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
                token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
                scopes=[
                    "offline_access",
                    "User.Read",
                    "Team.ReadBasic.All",
                    "Channel.ReadBasic.All",
                    "ChannelMessage.Read.All",
                    "ChannelMessage.Send",
                    "Chat.ReadWrite",
                    "ChatMessage.Send",
                    "Schedule.Read.All",
                    "Mail.Read",
                ],
                token_auth_method="body",
            ),
            test_endpoint=TestEndpoint(
                url="https://graph.microsoft.com/v1.0/me",
                method="GET",
                headers={"Authorization": "Bearer {access_token}"},
                success_indicators=SuccessIndicators(
                    status_codes=[200],
                    response_fields=["id"],
                ),
                cost_level="free",
                description=(
                    "Validates the access token by fetching the authenticated "
                    "user via Microsoft Graph."
                ),
            ),
        ),
    ],
)
