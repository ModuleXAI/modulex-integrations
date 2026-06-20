"""Pulse integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.pulse.manifest import manifest
from modulex_integrations.tools.pulse.tools import parser

TOOLS = (parser,)

__all__ = ["TOOLS", "manifest", "parser"]
