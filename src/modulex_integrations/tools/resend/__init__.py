"""Resend integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.resend.manifest import manifest
from modulex_integrations.tools.resend.tools import (
    create_contact,
    delete_contact,
    get_contact,
    get_email,
    list_contacts,
    list_domains,
    send,
    update_contact,
)

TOOLS = (
    send,
    get_email,
    create_contact,
    list_contacts,
    get_contact,
    update_contact,
    delete_contact,
    list_domains,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "delete_contact",
    "get_contact",
    "get_email",
    "list_contacts",
    "list_domains",
    "manifest",
    "send",
    "update_contact",
]
