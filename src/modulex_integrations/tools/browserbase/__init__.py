"""Browserbase integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.browserbase.manifest import manifest
from modulex_integrations.tools.browserbase.tools import (
    create_context,
    create_session,
    list_projects,
)

TOOLS = (
    create_context,
    create_session,
    list_projects,
)

__all__ = [
    "TOOLS",
    "create_context",
    "create_session",
    "list_projects",
    "manifest",
]
