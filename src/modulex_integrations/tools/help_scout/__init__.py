"""Help Scout integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.help_scout.manifest import manifest
from modulex_integrations.tools.help_scout.tools import (
    add_note,
    create_customer,
    get_conversation_details,
    get_conversation_threads,
    get_tag_by_id,
    list_tags,
    send_reply,
    update_conversation,
)

TOOLS = (
    add_note,
    create_customer,
    get_conversation_details,
    get_conversation_threads,
    get_tag_by_id,
    list_tags,
    send_reply,
    update_conversation,
)

__all__ = [
    "TOOLS",
    "add_note",
    "create_customer",
    "get_conversation_details",
    "get_conversation_threads",
    "get_tag_by_id",
    "list_tags",
    "manifest",
    "send_reply",
    "update_conversation",
]
