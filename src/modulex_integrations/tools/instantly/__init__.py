"""Instantly integration — discovered by modulex via the
``modulex.tools`` entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.instantly.manifest import manifest
from modulex_integrations.tools.instantly.tools import (
    activate_campaign,
    create_campaign,
    create_lead,
    create_lead_list,
    delete_leads,
    get_lead,
    list_campaigns,
    list_emails,
    list_lead_lists,
    list_leads,
    patch_campaign,
    reply_to_email,
    update_lead_interest_status,
)

TOOLS = (
    list_leads,
    get_lead,
    create_lead,
    delete_leads,
    update_lead_interest_status,
    list_campaigns,
    create_campaign,
    patch_campaign,
    activate_campaign,
    list_emails,
    reply_to_email,
    list_lead_lists,
    create_lead_list,
)

__all__ = [
    "TOOLS",
    "activate_campaign",
    "create_campaign",
    "create_lead",
    "create_lead_list",
    "delete_leads",
    "get_lead",
    "list_campaigns",
    "list_emails",
    "list_lead_lists",
    "list_leads",
    "manifest",
    "patch_campaign",
    "reply_to_email",
    "update_lead_interest_status",
]
