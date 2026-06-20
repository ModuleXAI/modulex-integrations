"""ZeroBounce integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.zerobounce.manifest import manifest
from modulex_integrations.tools.zerobounce.tools import get_credits, verify_email

TOOLS = (verify_email, get_credits)

__all__ = ["TOOLS", "get_credits", "manifest", "verify_email"]
