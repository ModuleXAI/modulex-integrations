"""Findymail integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS`` (tuple of
LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.findymail.manifest import manifest
from modulex_integrations.tools.findymail.tools import (
    find_email_from_linkedin,
    find_email_from_name,
    find_emails_by_domain,
    find_employees,
    find_phone,
    get_company,
    get_credits,
    lookup_technologies,
    reverse_email_lookup,
    search_technologies,
    verify_email,
)

TOOLS = (
    find_email_from_name,
    find_email_from_linkedin,
    find_emails_by_domain,
    verify_email,
    reverse_email_lookup,
    get_company,
    find_employees,
    find_phone,
    search_technologies,
    lookup_technologies,
    get_credits,
)

__all__ = [
    "TOOLS",
    "find_email_from_linkedin",
    "find_email_from_name",
    "find_emails_by_domain",
    "find_employees",
    "find_phone",
    "get_company",
    "get_credits",
    "lookup_technologies",
    "manifest",
    "reverse_email_lookup",
    "search_technologies",
    "verify_email",
]
