"""Google Contacts integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.google_contacts.manifest import manifest
from modulex_integrations.tools.google_contacts.tools import (
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    list_directory_contacts,
    update_contact,
)

TOOLS = (
    create_contact,
    delete_contact,
    get_contact,
    list_contacts,
    list_directory_contacts,
    update_contact,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "delete_contact",
    "get_contact",
    "list_contacts",
    "list_directory_contacts",
    "manifest",
    "update_contact",
]
