"""Sixtyfour AI integration — discovered by modulex via the
``modulex.tools`` entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.sixtyfour.manifest import manifest
from modulex_integrations.tools.sixtyfour.tools import (
    enrich_company,
    enrich_lead,
    find_email,
    find_phone,
)

TOOLS = (find_phone, find_email, enrich_lead, enrich_company)

__all__ = [
    "TOOLS",
    "enrich_company",
    "enrich_lead",
    "find_email",
    "find_phone",
    "manifest",
]
