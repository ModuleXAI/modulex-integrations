"""Greptile integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS`` (tuple of
LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.greptile.manifest import manifest
from modulex_integrations.tools.greptile.tools import index_repo, query, search, status

TOOLS = (query, search, index_repo, status)

__all__ = ["TOOLS", "index_repo", "manifest", "query", "search", "status"]
