"""Intercom integration."""
from modulex_integrations.tools.intercom.manifest import manifest
from modulex_integrations.tools.intercom.tools import (
    add_tag_to_contact,
    create_note,
    get_contact,
    get_conversation,
    list_admins,
    list_conversations,
    list_tags,
    reply_to_conversation,
    search_contacts,
    search_conversations,
    send_incoming_message,
    send_message_to_contact,
    upsert_contact,
)

TOOLS = (
    get_contact,
    search_contacts,
    upsert_contact,
    create_note,
    add_tag_to_contact,
    list_tags,
    list_admins,
    get_conversation,
    list_conversations,
    search_conversations,
    send_incoming_message,
    send_message_to_contact,
    reply_to_conversation,
)

__all__ = [
    "TOOLS",
    "add_tag_to_contact",
    "create_note",
    "get_contact",
    "get_conversation",
    "list_admins",
    "list_conversations",
    "list_tags",
    "manifest",
    "reply_to_conversation",
    "search_contacts",
    "search_conversations",
    "send_incoming_message",
    "send_message_to_contact",
    "upsert_contact",
]
