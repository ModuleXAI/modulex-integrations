"""Dropcontact integration — discovered by modulex via the
``modulex.tools`` entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.dropcontact.manifest import manifest
from modulex_integrations.tools.dropcontact.tools import enrich_contact

TOOLS = (enrich_contact,)

__all__ = ["TOOLS", "enrich_contact", "manifest"]
