"""Flint integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.flint.manifest import manifest
from modulex_integrations.tools.flint.tools import (
    create_task,
    generate_pages,
    get_task,
)

TOOLS = (
    create_task,
    generate_pages,
    get_task,
)

__all__ = [
    "TOOLS",
    "create_task",
    "generate_pages",
    "get_task",
    "manifest",
]
