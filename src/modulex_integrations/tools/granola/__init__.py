"""Granola integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.granola.manifest import manifest
from modulex_integrations.tools.granola.tools import get_note, list_folders, list_notes

TOOLS = (list_notes, get_note, list_folders)

__all__ = ["TOOLS", "get_note", "list_folders", "list_notes", "manifest"]
