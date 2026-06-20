"""Mem0 integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.mem0.manifest import manifest
from modulex_integrations.tools.mem0.tools import add_memories, get_memories, search_memories

TOOLS = (add_memories, search_memories, get_memories)

__all__ = ["TOOLS", "add_memories", "get_memories", "manifest", "search_memories"]
