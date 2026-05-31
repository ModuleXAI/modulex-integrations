"""Fellow integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.fellow.manifest import manifest
from modulex_integrations.tools.fellow.tools import (
    archive_action_item,
    complete_action_item,
    get_note_by_id,
)

TOOLS = (
    archive_action_item,
    complete_action_item,
    get_note_by_id,
)

__all__ = [
    "TOOLS",
    "archive_action_item",
    "complete_action_item",
    "get_note_by_id",
    "manifest",
]
