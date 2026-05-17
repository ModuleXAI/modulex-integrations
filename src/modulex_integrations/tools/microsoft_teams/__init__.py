"""Microsoft Teams integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_teams.manifest import manifest
from modulex_integrations.tools.microsoft_teams.tools import (
    create_channel,
    get_chat_message,
    get_current_user,
    list_channel_messages,
    list_channels,
    list_chats,
    list_messages_in_chat,
    list_shifts,
    list_teams,
    search_messages,
    send_channel_message,
    send_chat_message,
)

TOOLS = (
    create_channel,
    get_chat_message,
    get_current_user,
    list_channel_messages,
    list_channels,
    list_chats,
    list_messages_in_chat,
    list_shifts,
    list_teams,
    search_messages,
    send_channel_message,
    send_chat_message,
)

__all__ = [
    "TOOLS",
    "create_channel",
    "get_chat_message",
    "get_current_user",
    "list_channel_messages",
    "list_channels",
    "list_chats",
    "list_messages_in_chat",
    "list_shifts",
    "list_teams",
    "manifest",
    "search_messages",
    "send_channel_message",
    "send_chat_message",
]
