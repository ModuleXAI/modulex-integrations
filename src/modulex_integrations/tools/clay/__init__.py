"""Clay integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.clay.manifest import manifest
from modulex_integrations.tools.clay.tools import populate

TOOLS = (populate,)

__all__ = ["TOOLS", "manifest", "populate"]
