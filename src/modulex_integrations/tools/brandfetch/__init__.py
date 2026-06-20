"""Brandfetch integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.brandfetch.manifest import manifest
from modulex_integrations.tools.brandfetch.tools import get_brand, search

TOOLS = (get_brand, search)

__all__ = ["TOOLS", "get_brand", "manifest", "search"]
