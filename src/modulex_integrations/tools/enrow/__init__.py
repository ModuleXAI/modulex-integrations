"""Enrow integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.enrow.manifest import manifest
from modulex_integrations.tools.enrow.tools import find_email, verify_email

TOOLS = (find_email, verify_email)

__all__ = ["TOOLS", "find_email", "manifest", "verify_email"]
