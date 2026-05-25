"""Mintlify integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.mintlify.manifest import manifest
from modulex_integrations.tools.mintlify.tools import (
    chat_with_assistant,
    search_documentation,
    trigger_update,
)

TOOLS = (
    chat_with_assistant,
    search_documentation,
    trigger_update,
)

__all__ = [
    "TOOLS",
    "chat_with_assistant",
    "manifest",
    "search_documentation",
    "trigger_update",
]
