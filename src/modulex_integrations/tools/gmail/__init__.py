"""Gmail integration."""
from modulex_integrations.tools.gmail.manifest import manifest
from modulex_integrations.tools.gmail.tools import (
    list_labels,
    send_message,
)

TOOLS = (
    send_message,
    list_labels,
)

__all__ = [
    "TOOLS",
    "list_labels",
    "manifest",
    "send_message",
]
