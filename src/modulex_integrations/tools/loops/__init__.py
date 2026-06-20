"""Loops integration — discovered by modulex via the ``modulex.tools``
entry point.

Public surface: ``manifest`` (IntegrationManifest) and ``TOOLS``
(tuple of LangChain ``StructuredTool`` objects, one per action).
"""
from modulex_integrations.tools.loops.manifest import manifest
from modulex_integrations.tools.loops.tools import (
    create_contact,
    create_contact_property,
    delete_contact,
    find_contact,
    list_contact_properties,
    list_mailing_lists,
    list_transactional_emails,
    send_event,
    send_transactional_email,
    update_contact,
)

TOOLS = (
    create_contact,
    update_contact,
    find_contact,
    delete_contact,
    send_transactional_email,
    send_event,
    list_mailing_lists,
    list_transactional_emails,
    create_contact_property,
    list_contact_properties,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "create_contact_property",
    "delete_contact",
    "find_contact",
    "list_contact_properties",
    "list_mailing_lists",
    "list_transactional_emails",
    "manifest",
    "send_event",
    "send_transactional_email",
    "update_contact",
]
