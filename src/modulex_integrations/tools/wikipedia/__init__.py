"""Wikipedia integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.wikipedia.manifest import manifest
from modulex_integrations.tools.wikipedia.tools import content, random, search, summary

TOOLS = (summary, search, content, random)

__all__ = ["TOOLS", "content", "manifest", "random", "search", "summary"]
