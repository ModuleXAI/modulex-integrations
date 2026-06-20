"""Wiza integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.wiza.manifest import manifest
from modulex_integrations.tools.wiza.tools import (
    company_enrichment,
    get_credits,
    individual_reveal,
    prospect_search,
)

TOOLS = (prospect_search, company_enrichment, individual_reveal, get_credits)

__all__ = [
    "TOOLS",
    "company_enrichment",
    "get_credits",
    "individual_reveal",
    "manifest",
    "prospect_search",
]
