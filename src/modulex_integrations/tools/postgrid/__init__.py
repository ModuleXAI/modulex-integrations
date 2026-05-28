"""PostGrid integration — discovered via the ``modulex.tools`` entry point."""
from modulex_integrations.tools.postgrid.manifest import manifest
from modulex_integrations.tools.postgrid.tools import (
    create_contact,
    create_letter,
    create_postcard,
)

TOOLS = (
    create_contact,
    create_letter,
    create_postcard,
)

__all__ = [
    "TOOLS",
    "create_contact",
    "create_letter",
    "create_postcard",
    "manifest",
]
