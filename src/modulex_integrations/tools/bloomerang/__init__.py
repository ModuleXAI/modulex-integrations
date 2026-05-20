"""Bloomerang integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.bloomerang.manifest import manifest
from modulex_integrations.tools.bloomerang.tools import (
    add_interaction,
    create_constituent,
    create_donation,
)

TOOLS = (
    create_constituent,
    create_donation,
    add_interaction,
)

__all__ = [
    "TOOLS",
    "add_interaction",
    "create_constituent",
    "create_donation",
    "manifest",
]
