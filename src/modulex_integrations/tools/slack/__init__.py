"""Slack integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.slack.manifest import manifest
from modulex_integrations.tools.slack.tools import (
    add_reaction,
    get_channel_history,
    get_thread_replies,
    get_user_profile,
    get_users,
    list_channels,
    post_message,
    reply_to_thread,
)

TOOLS = (
    list_channels,
    post_message,
    reply_to_thread,
    add_reaction,
    get_channel_history,
    get_thread_replies,
    get_users,
    get_user_profile,
)

__all__ = [
    "TOOLS",
    "add_reaction",
    "get_channel_history",
    "get_thread_replies",
    "get_user_profile",
    "get_users",
    "list_channels",
    "manifest",
    "post_message",
    "reply_to_thread",
]
