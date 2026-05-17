"""Exa integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.exa.manifest import manifest
from modulex_integrations.tools.exa.tools import answer, find_similar, get_contents, search

TOOLS = (search, get_contents, find_similar, answer)

__all__ = ["TOOLS", "answer", "find_similar", "get_contents", "manifest", "search"]
