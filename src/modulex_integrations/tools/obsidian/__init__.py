"""Obsidian integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.obsidian.manifest import manifest
from modulex_integrations.tools.obsidian.tools import (
    append_active,
    append_note,
    append_periodic_note,
    create_note,
    delete_note,
    execute_command,
    get_active,
    get_note,
    get_periodic_note,
    list_commands,
    list_files,
    open_file,
    patch_active,
    patch_note,
    search,
)

TOOLS = (
    list_files,
    get_note,
    create_note,
    append_note,
    patch_note,
    delete_note,
    search,
    get_active,
    append_active,
    patch_active,
    open_file,
    list_commands,
    execute_command,
    get_periodic_note,
    append_periodic_note,
)

__all__ = [
    "TOOLS",
    "append_active",
    "append_note",
    "append_periodic_note",
    "create_note",
    "delete_note",
    "execute_command",
    "get_active",
    "get_note",
    "get_periodic_note",
    "list_commands",
    "list_files",
    "manifest",
    "open_file",
    "patch_active",
    "patch_note",
    "search",
]
