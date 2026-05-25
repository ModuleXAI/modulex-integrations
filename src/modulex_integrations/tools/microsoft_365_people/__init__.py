"""Microsoft 365 People integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.microsoft_365_people.manifest import manifest
from modulex_integrations.tools.microsoft_365_people.tools import (
    create_contact,
    create_contact_folder,
    update_contact,
)

TOOLS = (
    create_contact,
    create_contact_folder,
    update_contact,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "create_contact_folder",
    "manifest",
    "update_contact",
]
