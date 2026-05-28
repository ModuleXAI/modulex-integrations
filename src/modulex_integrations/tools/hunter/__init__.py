"""Hunter integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.hunter.manifest import manifest
from modulex_integrations.tools.hunter.tools import (
    account_information,
    combined_enrichment,
    create_lead,
    delete_lead,
    domain_search,
    email_count,
    email_finder,
    email_verifier,
    get_lead,
    get_leads_list,
    list_leads,
    list_leads_lists,
    update_lead,
)

TOOLS = (
    account_information,
    combined_enrichment,
    create_lead,
    delete_lead,
    domain_search,
    email_count,
    email_finder,
    email_verifier,
    get_lead,
    get_leads_list,
    list_leads,
    list_leads_lists,
    update_lead,
)

__all__ = [
    "TOOLS",
    "account_information",
    "combined_enrichment",
    "create_lead",
    "delete_lead",
    "domain_search",
    "email_count",
    "email_finder",
    "email_verifier",
    "get_lead",
    "get_leads_list",
    "list_leads",
    "list_leads_lists",
    "manifest",
    "update_lead",
]
