"""Insightly integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.insightly.manifest import manifest
from modulex_integrations.tools.insightly.tools import (
    create_contact,
    create_task,
)

TOOLS = (
    create_contact,
    create_task,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "create_task",
    "manifest",
]
