"""Telegram Bot integration manifest."""
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


def _chat_required() -> ParameterDef:
    return ParameterDef(
        type="string",
        description="Unique identifier for the target chat or @username of the target channel",
        required=True,
    )


def _send_common_params() -> dict[str, ParameterDef]:
    return {
        "parse_mode": ParameterDef(
            type="string",
            description="Mode for parsing entities ('Markdown', 'MarkdownV2', or 'HTML')",
        ),
        "disable_notification": ParameterDef(
            type="boolean",
            description="Send silently with no sound",
            default=False,
        ),
        "reply_to_message_id": ParameterDef(
            type="integer",
            description="ID of the message to reply to",
        ),
    }


manifest = IntegrationManifest(
    name="telegram",
    display_name="Telegram Bot",
    description=(
        "Send messages, manage chats, and interact with users via "
        "Telegram Bot API. Supports text messages, media, chat "
        "management, and user moderation."
    ),
    version="1.0.0",
    author="ModuleX",
    logo="logos:telegram",
    app_url="https://core.telegram.org/bots/api",
    categories=[
        "Communication",
        "Communication & Collaboration",
        "automation",
        "development",
        "social_media",
        "messaging",
    ],
    actions=[
        ActionDefinition(
            name="send_text_message",
            description=(
                "Send a text message to a Telegram chat. Supports Markdown, "
                "MarkdownV2, and HTML formatting."
            ),
            parameters={
                "chat_id": _chat_required(),
                "text": ParameterDef(
                    type="string",
                    description="Text of the message (1-4096 characters)",
                    required=True,
                ),
                **_send_common_params(),
            },
        ),
        ActionDefinition(
            name="send_photo",
            description=(
                "Send a photo to a Telegram chat. Photos can be sent by "
                "URL or file_id."
            ),
            parameters={
                "chat_id": _chat_required(),
                "photo": ParameterDef(
                    type="string",
                    description="Photo to send (file_id or HTTP URL)",
                    required=True,
                ),
                "caption": ParameterDef(
                    type="string", description="Photo caption (0-1024 characters)"
                ),
                **_send_common_params(),
            },
        ),
        ActionDefinition(
            name="send_document",
            description="Send a document or file to a Telegram chat.",
            parameters={
                "chat_id": _chat_required(),
                "document": ParameterDef(
                    type="string",
                    description="Document to send (file_id or HTTP URL)",
                    required=True,
                ),
                "caption": ParameterDef(
                    type="string", description="Document caption (0-1024 characters)"
                ),
                **_send_common_params(),
            },
        ),
        ActionDefinition(
            name="send_video",
            description="Send a video to a Telegram chat.",
            parameters={
                "chat_id": _chat_required(),
                "video": ParameterDef(
                    type="string",
                    description="Video to send (file_id or HTTP URL)",
                    required=True,
                ),
                "caption": ParameterDef(
                    type="string", description="Video caption (0-1024 characters)"
                ),
                "duration": ParameterDef(
                    type="integer", description="Duration of sent video in seconds"
                ),
                **_send_common_params(),
            },
        ),
        ActionDefinition(
            name="send_audio",
            description="Send an audio file to a Telegram chat.",
            parameters={
                "chat_id": _chat_required(),
                "audio": ParameterDef(
                    type="string",
                    description="Audio to send (file_id or HTTP URL)",
                    required=True,
                ),
                "caption": ParameterDef(
                    type="string", description="Audio caption (0-1024 characters)"
                ),
                "duration": ParameterDef(
                    type="integer", description="Duration of the audio in seconds"
                ),
                "performer": ParameterDef(
                    type="string", description="Performer of the audio"
                ),
                "title": ParameterDef(type="string", description="Track name"),
                "disable_notification": ParameterDef(
                    type="boolean",
                    description="Send silently",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="forward_message",
            description="Forward a message from one chat to another.",
            parameters={
                "chat_id": _chat_required(),
                "from_chat_id": ParameterDef(
                    type="string",
                    description="Chat where the original message was sent",
                    required=True,
                ),
                "message_id": ParameterDef(
                    type="integer",
                    description="Message identifier in from_chat_id",
                    required=True,
                ),
                "disable_notification": ParameterDef(
                    type="boolean",
                    description="Send silently",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="edit_text_message",
            description="Edit a text message previously sent by the bot.",
            parameters={
                "chat_id": _chat_required(),
                "message_id": ParameterDef(
                    type="integer",
                    description="Identifier of the message to edit",
                    required=True,
                ),
                "text": ParameterDef(
                    type="string",
                    description="New text of the message (1-4096 characters)",
                    required=True,
                ),
                "parse_mode": ParameterDef(
                    type="string", description="Mode for parsing entities"
                ),
            },
        ),
        ActionDefinition(
            name="delete_message",
            description=(
                "Delete a message from a chat (messages older than 48 hours "
                "cannot be deleted)."
            ),
            parameters={
                "chat_id": _chat_required(),
                "message_id": ParameterDef(
                    type="integer",
                    description="Identifier of the message to delete",
                    required=True,
                ),
            },
        ),
        ActionDefinition(
            name="pin_message",
            description=(
                "Pin a message in a chat. Bot must be an administrator with "
                "can_pin_messages permission."
            ),
            parameters={
                "chat_id": _chat_required(),
                "message_id": ParameterDef(
                    type="integer",
                    description="Identifier of the message to pin",
                    required=True,
                ),
                "disable_notification": ParameterDef(
                    type="boolean",
                    description="Pin silently",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_chat_member_count",
            description="Get the number of members in a chat.",
            parameters={"chat_id": _chat_required()},
        ),
        ActionDefinition(
            name="get_chat_administrators",
            description="Get a list of administrators in a chat with their permissions.",
            parameters={"chat_id": _chat_required()},
        ),
        ActionDefinition(
            name="get_updates",
            description=(
                "Get incoming updates via long polling: messages, edited "
                "messages, channel posts, and other events."
            ),
            parameters={
                "offset": ParameterDef(
                    type="integer",
                    description="Identifier of the first update to be returned",
                ),
                "limit": ParameterDef(
                    type="integer",
                    description="Number of updates to retrieve (1-100)",
                    default=100,
                ),
                "timeout": ParameterDef(
                    type="integer",
                    description="Timeout in seconds for long polling",
                    default=0,
                ),
            },
        ),
        ActionDefinition(
            name="ban_chat_member",
            description=(
                "Ban a user from a group, supergroup, or channel. Bot must "
                "be an administrator."
            ),
            parameters={
                "chat_id": _chat_required(),
                "user_id": ParameterDef(
                    type="integer",
                    description="Unique identifier of the target user",
                    required=True,
                ),
                "until_date": ParameterDef(
                    type="integer",
                    description="Date when the user will be unbanned (Unix time)",
                ),
                "revoke_messages": ParameterDef(
                    type="boolean",
                    description="Delete all messages from the chat for the user",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="unban_chat_member",
            description="Unban a previously banned user.",
            parameters={
                "chat_id": _chat_required(),
                "user_id": ParameterDef(
                    type="integer",
                    description="Unique identifier of the target user",
                    required=True,
                ),
                "only_if_banned": ParameterDef(
                    type="boolean",
                    description="Do nothing if the user is not banned",
                    default=True,
                ),
            },
        ),
        ActionDefinition(
            name="create_chat_invite_link",
            description=(
                "Create an additional invite link for a chat. Bot must have "
                "can_invite_users permission."
            ),
            parameters={
                "chat_id": _chat_required(),
                "name": ParameterDef(
                    type="string", description="Invite link name (0-32 characters)"
                ),
                "expire_date": ParameterDef(
                    type="integer",
                    description="Unix timestamp when the link will expire",
                ),
                "member_limit": ParameterDef(
                    type="integer",
                    description="Maximum number of users (1-99999)",
                ),
                "creates_join_request": ParameterDef(
                    type="boolean",
                    description="Users joining need admin approval",
                    default=False,
                ),
            },
        ),
        ActionDefinition(
            name="get_chat",
            description=(
                "Get up-to-date information about a chat including title, "
                "description, photo, and settings."
            ),
            parameters={"chat_id": _chat_required()},
        ),
        ActionDefinition(
            name="get_me",
            description=(
                "Get basic information about the bot — its username, name, "
                "and capabilities."
            ),
            parameters={},
        ),
    ],
    auth_schemas=[
        ApiKeyAuthSchema(
            display_name="Bot Token Authentication",
            description="Authenticate using your Telegram Bot token from @BotFather",
            setup_environment_variables=[
                EnvVar(
                    name="TELEGRAM_BOT_TOKEN",
                    display_name="Telegram Bot Token",
                    description="Your Telegram Bot token obtained from @BotFather",
                    required=True,
                    sensitive=True,
                ),
            ],
            test_endpoint=TestEndpoint(
                # Telegram is unusual: the bot token lives *inside* the URL
                # path (/bot{token}/getMe). Double-brace form is what the
                # legacy JSON used; the modulex runtime substitutes both
                # single- and double-brace placeholders.
                url="https://api.telegram.org/bot{api_key}/getMe",
                method="GET",
                headers={"Content-Type": "application/json"},
                success_indicators=SuccessIndicators(status_codes=[200]),
                cost_level="free",
                description="Validates bot token by calling getMe",
            ),
        ),
    ],
)
