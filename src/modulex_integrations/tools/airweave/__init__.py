"""Airweave integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.airweave.manifest import manifest
from modulex_integrations.tools.airweave.tools import search

TOOLS = (search,)

__all__ = ["TOOLS", "manifest", "search"]
