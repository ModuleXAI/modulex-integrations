"""Gmail integration."""
from modulex_integrations.tools.gmail.manifest import manifest
from modulex_integrations.tools.gmail.tools import (
    add_label,
    archive_message,
    create_draft,
    delete_message,
    list_labels,
    list_messages,
    mark_as_read,
    mark_as_unread,
    read_message,
    remove_label,
    search_messages,
    send_message,
    unarchive_message,
)

TOOLS = (
    send_message,
    read_message,
    search_messages,
    list_messages,
    create_draft,
    mark_as_read,
    mark_as_unread,
    archive_message,
    unarchive_message,
    delete_message,
    add_label,
    remove_label,
    list_labels,
)

__all__ = [
    "TOOLS",
    "add_label",
    "archive_message",
    "create_draft",
    "delete_message",
    "list_labels",
    "list_messages",
    "manifest",
    "mark_as_read",
    "mark_as_unread",
    "read_message",
    "remove_label",
    "search_messages",
    "send_message",
    "unarchive_message",
]
